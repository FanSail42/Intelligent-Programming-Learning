import math
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.learning import KnowledgePoint, UserKpMastery, WrongQuestionBook
from app.services.learning_cache import clear_dashboard_cache

CODE_ERROR_WEIGHT = 1.0
CHAT_NO_CONTEXT_WEIGHT = 0.6
DECAY_DAYS = 30.0
PENALTY_SCALE = 20.0


def compute_kp_score(
    penalties: list[tuple[float, datetime]],
    *,
    now: datetime | None = None,
) -> int:
    if not penalties:
        return 100
    ref = now or datetime.now()
    total = 0.0
    for weight, created_at in penalties:
        days = max(0, (ref - created_at).days)
        total += weight * math.exp(-days / DECAY_DAYS)
    return max(0, int(round(100 - total * PENALTY_SCALE)))


def weight_for_source(source_type: str) -> float:
    if source_type == "code_submission":
        return CODE_ERROR_WEIGHT
    if source_type == "chat_message":
        return CHAT_NO_CONTEXT_WEIGHT
    return 0.5


def refresh_user_mastery(
    db: Session,
    *,
    user_id: int,
    kp_id: int | None = None,
) -> None:
    if kp_id is None:
        kp_ids = [
            row[0]
            for row in db.query(KnowledgePoint.id)
            .filter(KnowledgePoint.deleted == 0)
            .all()
        ]
        for kid in kp_ids:
            _refresh_one_kp(db, user_id=user_id, kp_id=kid)
        clear_dashboard_cache(user_id)
        return
    _refresh_one_kp(db, user_id=user_id, kp_id=kp_id)
    clear_dashboard_cache(user_id)


def _refresh_one_kp(db: Session, *, user_id: int, kp_id: int) -> None:
    wrong_rows = (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == user_id,
            WrongQuestionBook.kp_id == kp_id,
            WrongQuestionBook.mastered == False,
            WrongQuestionBook.deleted == 0,
        )
        .all()
    )
    penalties = [
        (weight_for_source(row.source_type.value), row.created_at) for row in wrong_rows
    ]
    score = compute_kp_score(penalties)
    mastery = (
        db.query(UserKpMastery)
        .filter(
            UserKpMastery.user_id == user_id,
            UserKpMastery.kp_id == kp_id,
            UserKpMastery.deleted == 0,
        )
        .first()
    )
    if mastery:
        mastery.score = score
    else:
        db.add(UserKpMastery(user_id=user_id, kp_id=kp_id, score=score))
    db.flush()


def get_weak_kps_for_user(
    db: Session,
    user_id: int,
    limit: int = 5,
    course_id: int | None = None,
) -> list[tuple[int, str, int, int]]:
    query = (
        db.query(UserKpMastery, KnowledgePoint)
        .join(KnowledgePoint, KnowledgePoint.id == UserKpMastery.kp_id)
        .filter(
            UserKpMastery.user_id == user_id,
            UserKpMastery.deleted == 0,
            KnowledgePoint.deleted == 0,
        )
    )
    if course_id is not None:
        query = query.filter(KnowledgePoint.course_id == course_id)
    rows = query.order_by(UserKpMastery.score.asc()).limit(limit).all()
    result: list[tuple[int, str, int, int]] = [
        (kp.id, kp.name, mastery.score, kp.course_id) for mastery, kp in rows
    ]

    if course_id is not None:
        existing_ids = {item[0] for item in result}
        course_kps = (
            db.query(KnowledgePoint)
            .filter(KnowledgePoint.course_id == course_id, KnowledgePoint.deleted == 0)
            .order_by(KnowledgePoint.sort_order.asc(), KnowledgePoint.id.asc())
            .all()
        )
        for kp in course_kps:
            if kp.id in existing_ids:
                continue
            mastery = (
                db.query(UserKpMastery)
                .filter(
                    UserKpMastery.user_id == user_id,
                    UserKpMastery.kp_id == kp.id,
                    UserKpMastery.deleted == 0,
                )
                .first()
            )
            score = mastery.score if mastery else 100
            result.append((kp.id, kp.name, score, kp.course_id))
            existing_ids.add(kp.id)
            if len(result) >= limit:
                break

    result.sort(key=lambda item: item[2])
    trimmed = result[:limit]

    if course_id is not None and not trimmed:
        return get_weak_kps_for_user(db, user_id, limit=limit, course_id=None)

    return trimmed
