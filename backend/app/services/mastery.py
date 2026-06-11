import math
from datetime import datetime

from sqlalchemy import case, func
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


def _kp_wrong_stats(
    db: Session,
    user_id: int,
    kp_ids: list[int],
) -> dict[int, dict[str, int]]:
    if not kp_ids:
        return {}
    rows = (
        db.query(
            WrongQuestionBook.kp_id,
            func.count(WrongQuestionBook.id).label("total"),
            func.sum(
                case((WrongQuestionBook.mastered == False, 1), else_=0)  # noqa: E712
            ).label("unmastered"),
        )
        .filter(
            WrongQuestionBook.user_id == user_id,
            WrongQuestionBook.kp_id.in_(kp_ids),
            WrongQuestionBook.deleted == 0,
        )
        .group_by(WrongQuestionBook.kp_id)
        .all()
    )
    stats: dict[int, dict[str, int]] = {}
    for kp_id, total, unmastered in rows:
        if kp_id is None:
            continue
        stats[int(kp_id)] = {
            "total": int(total or 0),
            "unmastered": int(unmastered or 0),
        }
    return stats


def compute_dashboard_kp_score(
    *,
    mastery_score: int,
    unmastered_wrong: int,
    total_wrong: int,
    sort_order: int,
    kp_id: int,
) -> int:
    """Spread scores for chart contrast while keeping weak KPs at the bottom."""
    score = mastery_score
    if unmastered_wrong:
        score = min(score, max(18, mastery_score - unmastered_wrong * 16))
    elif total_wrong:
        score = min(score, mastery_score - 8)

    if score >= 95:
        spread = 90 - sort_order * 6 - (kp_id % 4) * 3
        score = max(52, min(score, spread))
    elif score >= 80:
        score = max(55, score - (sort_order % 3) * 4 - (kp_id % 2) * 2)
    return int(max(0, min(100, score)))


def get_dashboard_weak_kps(
    db: Session,
    user_id: int,
    limit: int = 8,
    course_id: int | None = None,
) -> list[tuple[int, str, int, int]]:
    base = get_weak_kps_for_user(db, user_id, limit=limit, course_id=course_id)
    if not base:
        return base

    kp_ids = [item[0] for item in base]
    wrong_stats = _kp_wrong_stats(db, user_id, kp_ids)
    kp_meta = {
        row.id: row.sort_order
        for row in db.query(KnowledgePoint)
        .filter(KnowledgePoint.id.in_(kp_ids), KnowledgePoint.deleted == 0)
        .all()
    }

    enriched: list[tuple[int, str, int, int]] = []
    for kp_id, name, mastery_score, cid in base:
        stat = wrong_stats.get(kp_id, {"total": 0, "unmastered": 0})
        display = compute_dashboard_kp_score(
            mastery_score=mastery_score,
            unmastered_wrong=stat["unmastered"],
            total_wrong=stat["total"],
            sort_order=kp_meta.get(kp_id, 0),
            kp_id=kp_id,
        )
        enriched.append((kp_id, name, display, cid))

    enriched.sort(key=lambda item: item[2])
    return enriched[:limit]
