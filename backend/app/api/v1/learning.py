from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import DbSession, require_roles
from app.models.code import AnalysisResult, CodeSubmission
from app.models.learning import WrongQuestionBook
from app.models.user import User, UserRole
from app.schemas.learning import (
    DashboardOut,
    DashboardSummary,
    LearningEventCreate,
    RecentEventItem,
    RecommendationItem,
    WeakKpItem,
    WrongBookItem,
    WrongBookMasteredUpdate,
    WrongBookStatsOut,
)
from app.schemas.response import PageResult, success
from app.services.learning_cache import get_dashboard_cache, set_dashboard_cache
from app.services.learning_events import count_events_7d, record_event
from app.services.dashboard_activity import build_recent_events
from app.services.mastery import get_dashboard_weak_kps, refresh_user_mastery
from app.services.recommendation import build_recommendations
from app.services.wrong_book_analysis import (
    apply_wrong_book_course_filter,
    backfill_wrong_book_course_ids,
    build_wrong_book_stats,
    enrich_wrong_book_row,
)

router = APIRouter(prefix="/learning", tags=["learning"])

StudentUser = Annotated[User, Depends(require_roles(UserRole.student))]


@router.post("/events")
def create_event(
    body: LearningEventCreate,
    db: DbSession,
    user: StudentUser,
) -> dict:
    record_event(
        db,
        user_id=user.id,
        event_type=body.event_type,
        course_id=body.course_id,
        kp_id=body.kp_id,
        payload=body.payload,
    )
    db.commit()
    return success(None)


@router.get("/dashboard")
def get_dashboard(
    db: DbSession,
    user: StudentUser,
    course_id: int | None = Query(None),
) -> dict:
    cached = get_dashboard_cache(user.id)
    if cached and course_id is None:
        return success(cached)

    refresh_user_mastery(db, user_id=user.id, kp_id=None)

    if cached and course_id is not None:
        weak = [
            WeakKpItem(kp_id=k, name=n, score=s, course_id=c)
            for k, n, s, c in get_dashboard_weak_kps(db, user.id, limit=8, course_id=course_id)
        ]
        recent = [
            RecentEventItem(**item)
            for item in build_recent_events(
                db, user_id=user.id, course_id=course_id, limit=10
            )
        ]
        payload = {
            **cached,
            "weak_kps": [w.model_dump() for w in weak],
            "recent_events": [r.model_dump(mode="json") for r in recent],
        }
        return success(payload)

    total_7d = count_events_7d(db, user.id)
    wrong_count = (
        db.query(WrongQuestionBook)
        .filter(WrongQuestionBook.user_id == user.id, WrongQuestionBook.deleted == 0)
        .count()
    )
    mastered_count = (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == user.id,
            WrongQuestionBook.mastered == True,
            WrongQuestionBook.deleted == 0,
        )
        .count()
    )
    weak = [
        WeakKpItem(kp_id=k, name=n, score=s, course_id=c)
        for k, n, s, c in get_dashboard_weak_kps(
            db, user.id, limit=8, course_id=course_id
        )
    ]
    recent = [
        RecentEventItem(**item)
        for item in build_recent_events(
            db, user_id=user.id, course_id=course_id, limit=10
        )
    ]
    out = DashboardOut(
        summary=DashboardSummary(
            total_events_7d=total_7d,
            wrong_count=wrong_count,
            mastered_count=mastered_count,
        ),
        weak_kps=weak,
        recent_events=recent,
    )
    payload = out.model_dump(mode="json")
    set_dashboard_cache(user.id, payload)
    return success(payload)


@router.get("/wrong-book/stats")
def wrong_book_stats(
    db: DbSession,
    user: StudentUser,
    course_id: int | None = Query(None),
    days: int = Query(30, ge=7, le=90),
) -> dict:
    backfill_wrong_book_course_ids(db, user_id=user.id)
    stats = build_wrong_book_stats(db, user.id, course_id=course_id, days=days)
    return success(WrongBookStatsOut.model_validate(stats).model_dump(mode="json"))


@router.get("/wrong-book")
def list_wrong_book(
    db: DbSession,
    user: StudentUser,
    course_id: int | None = Query(None),
    mastered: bool | None = Query(None),
    category: str | None = Query(None),
    page_num: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> dict:
    backfill_wrong_book_course_ids(db, user_id=user.id)
    query = db.query(WrongQuestionBook).filter(
        WrongQuestionBook.user_id == user.id,
        WrongQuestionBook.deleted == 0,
    )
    query = apply_wrong_book_course_filter(query, course_id, db)
    if mastered is not None:
        query = query.filter(WrongQuestionBook.mastered == mastered)

    rows = query.order_by(WrongQuestionBook.id.desc()).all()

    submission_ids = [
        row.ref_id for row in rows if row.source_type.value == "code_submission"
    ]
    from app.services.wrong_book_analysis import _load_analysis_map, _load_kp_map

    analysis_map = _load_analysis_map(db, submission_ids)
    kp_map = _load_kp_map(db, [row.kp_id for row in rows if row.kp_id])

    if category:
        filtered = []
        for row in rows:
            analysis = (
                analysis_map.get(row.ref_id)
                if row.source_type.value == "code_submission"
                else None
            )
            from app.services.wrong_book_analysis import detect_category

            if detect_category(row.source_type.value, analysis=analysis) == category:
                filtered.append(row)
        rows = filtered

    total = len(rows)
    page_rows = rows[(page_num - 1) * page_size : page_num * page_size]

    items: list[WrongBookItem] = []
    for row in page_rows:
        extra = enrich_wrong_book_row(
            db, row, analysis_map=analysis_map, kp_map=kp_map
        )
        items.append(
            WrongBookItem(
                id=row.id,
                source_type=row.source_type.value,
                ref_id=row.ref_id,
                course_id=row.course_id,
                kp_id=row.kp_id,
                kp_name=extra.get("kp_name"),
                language=extra.get("language"),
                summary=extra.get("summary"),
                category=extra.get("category"),
                category_label=extra.get("category_label"),
                issues=extra.get("issues") or [],
                suggestions=extra.get("suggestions") or [],
                review_tip=extra.get("review_tip"),
                has_fixed_code=bool(extra.get("has_fixed_code")),
                mastered=row.mastered,
                created_at=row.created_at,
            )
        )
    page = PageResult(list=items, total=total, page_num=page_num, page_size=page_size)
    return success(page.model_dump(mode="json"))


@router.put("/wrong-book/{item_id}/mastered")
def update_wrong_book_mastered(
    item_id: int,
    body: WrongBookMasteredUpdate,
    db: DbSession,
    user: StudentUser,
) -> dict:
    row = (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.id == item_id,
            WrongQuestionBook.user_id == user.id,
            WrongQuestionBook.deleted == 0,
        )
        .first()
    )
    if not row:
        from app.core.exceptions import ERR_NOT_FOUND, BusinessException

        raise BusinessException(ERR_NOT_FOUND, "错题记录不存在")
    row.mastered = body.mastered
    refresh_user_mastery(db, user_id=user.id, kp_id=row.kp_id)
    db.commit()
    return success({"id": row.id, "mastered": row.mastered})


@router.get("/recommendations")
def get_recommendations(
    db: DbSession,
    user: StudentUser,
    course_id: int = Query(...),
) -> dict:
    raw = build_recommendations(db, user, course_id)
    items = [RecommendationItem(**item) for item in raw]
    return success([i.model_dump() for i in items])
