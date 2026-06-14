"""Class-level learning analytics for teacher dashboard (M07)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.course import Course, CourseStudent
from app.models.learning import KnowledgePoint, LearningEvent, UserKpMastery, WrongQuestionBook
from app.models.user import User
from app.services.mastery import refresh_user_mastery
from app.services.wrong_book_analysis import (
    _load_analysis_map,
    _load_kp_map,
    apply_wrong_book_course_filter,
    backfill_wrong_book_course_ids,
    build_item_detail,
    CATEGORY_LABELS,
    CATEGORY_TIPS,
    detect_category,
    enrich_wrong_book_row,
    SOURCE_LABELS,
    SOURCE_TYPES_ORDER,
)


def _get_teacher_name(db: Session, teacher_id: int) -> str:
    teacher = db.query(User).filter(User.id == teacher_id, User.deleted == 0).first()
    return teacher.username if teacher else ""


def _enrolled_student_ids(db: Session, course_id: int) -> list[int]:
    return [
        row[0]
        for row in db.query(CourseStudent.user_id)
        .filter(CourseStudent.course_id == course_id, CourseStudent.deleted == 0)
        .all()
    ]


def _wrong_counts_for_student(
    db: Session,
    *,
    user_id: int,
    course_id: int,
) -> tuple[int, int]:
    backfill_wrong_book_course_ids(db, user_id=user_id)
    query = db.query(WrongQuestionBook).filter(
        WrongQuestionBook.user_id == user_id,
        WrongQuestionBook.deleted == 0,
    )
    query = apply_wrong_book_course_filter(query, course_id, db)
    rows = query.all()
    total = len(rows)
    unmastered = sum(1 for row in rows if not row.mastered)
    return total, unmastered


def load_enrolled_students(db: Session, course_id: int) -> list[dict]:
    rows = (
        db.query(CourseStudent, User)
        .join(User, User.id == CourseStudent.user_id)
        .filter(
            CourseStudent.course_id == course_id,
            CourseStudent.deleted == 0,
            User.deleted == 0,
        )
        .order_by(CourseStudent.joined_at.asc(), CourseStudent.id.asc())
        .all()
    )
    result: list[dict] = []
    for enrollment, user in rows:
        wrong_total, unmastered = _wrong_counts_for_student(
            db, user_id=user.id, course_id=course_id
        )
        result.append(
            {
                "user_id": user.id,
                "username": user.username,
                "joined_at": enrollment.joined_at,
                "wrong_count": wrong_total,
                "unmastered_count": unmastered,
            }
        )
    return result


def _empty_wrong_book_stats(days: int) -> dict[str, Any]:
    today = date.today()
    start = today - timedelta(days=days - 1)
    trend = [
        {"date": (start + timedelta(days=i)).isoformat(), "count": 0}
        for i in range(days)
    ]
    return {
        "summary": {
            "total": 0,
            "mastered": 0,
            "unmastered": 0,
            "mastery_rate": 0,
        },
        "by_category": [],
        "by_source": [
            {"source_type": key, "label": SOURCE_LABELS[key], "count": 0}
            for key in SOURCE_TYPES_ORDER
        ],
        "by_language": [],
        "by_kp": [],
        "trend": trend,
        "mastered_pie": [
            {"name": "未掌握", "value": 0},
            {"name": "已掌握", "value": 0},
        ],
    }


def build_class_wrong_book_stats(
    db: Session,
    course_id: int,
    *,
    student_ids: list[int] | None = None,
    days: int = 7,
) -> dict[str, Any]:
    if student_ids is None:
        student_ids = _enrolled_student_ids(db, course_id)
    if not student_ids:
        return _empty_wrong_book_stats(days)

    for uid in student_ids:
        backfill_wrong_book_course_ids(db, user_id=uid)

    query = db.query(WrongQuestionBook).filter(
        WrongQuestionBook.user_id.in_(student_ids),
        WrongQuestionBook.deleted == 0,
    )
    query = apply_wrong_book_course_filter(query, course_id, db)
    rows = query.order_by(WrongQuestionBook.id.desc()).all()

    submission_ids = [
        row.ref_id for row in rows if row.source_type.value == "code_submission"
    ]
    analysis_map = _load_analysis_map(db, submission_ids)
    kp_ids = [row.kp_id for row in rows if row.kp_id]
    kp_map = _load_kp_map(db, kp_ids)

    total = len(rows)
    mastered = sum(1 for row in rows if row.mastered)
    unmastered = total - mastered

    by_category: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "unmastered": 0, "sample_issues": []}
    )
    by_source: dict[str, int] = defaultdict(int)
    by_language: dict[str, int] = defaultdict(int)
    by_kp: dict[int, dict[str, Any]] = defaultdict(lambda: {"total": 0, "unmastered": 0})

    today = date.today()
    start = today - timedelta(days=days - 1)
    trend_map: dict[str, int] = {
        (start + timedelta(days=i)).isoformat(): 0 for i in range(days)
    }

    for row in rows:
        analysis = (
            analysis_map.get(row.ref_id)
            if row.source_type.value == "code_submission"
            else None
        )
        category = detect_category(row.source_type.value, analysis=analysis)
        by_category[category]["total"] += 1
        if not row.mastered:
            by_category[category]["unmastered"] += 1

        detail = build_item_detail(row.source_type.value, analysis=analysis)
        for issue in detail.get("issues", [])[:2]:
            samples = by_category[category]["sample_issues"]
            msg = issue.get("message")
            if msg and msg not in samples and len(samples) < 3:
                samples.append(msg)

        by_source[row.source_type.value] += 1

        enriched = enrich_wrong_book_row(
            db, row, analysis_map=analysis_map, kp_map=kp_map
        )
        if enriched.get("language"):
            by_language[enriched["language"]] += 1

        if row.kp_id:
            kp_entry = by_kp[row.kp_id]
            kp_entry["kp_id"] = row.kp_id
            kp_entry["kp_name"] = kp_map.get(row.kp_id, f"知识点#{row.kp_id}")
            kp_entry["total"] += 1
            if not row.mastered:
                kp_entry["unmastered"] += 1

        if row.created_at:
            day_key = row.created_at.date().isoformat()
            if day_key in trend_map:
                trend_map[day_key] += 1

    category_list = []
    for key, label in CATEGORY_LABELS.items():
        stat = by_category.get(key)
        if not stat or stat["total"] == 0:
            continue
        category_list.append(
            {
                "category": key,
                "label": label,
                "total": stat["total"],
                "unmastered": stat["unmastered"],
                "analysis": CATEGORY_TIPS.get(key, ""),
                "sample_issues": stat["sample_issues"],
            }
        )
    category_list.sort(key=lambda x: x["unmastered"], reverse=True)

    return {
        "summary": {
            "total": total,
            "mastered": mastered,
            "unmastered": unmastered,
            "mastery_rate": round(mastered / total * 100, 1) if total else 0,
        },
        "by_category": category_list,
        "by_source": [
            {
                "source_type": key,
                "label": SOURCE_LABELS[key],
                "count": by_source.get(key, 0),
            }
            for key in SOURCE_TYPES_ORDER
        ],
        "by_language": [
            {"language": k, "count": v}
            for k, v in sorted(by_language.items(), key=lambda x: -x[1])
        ],
        "by_kp": sorted(
            list(by_kp.values()),
            key=lambda x: x.get("unmastered", 0),
            reverse=True,
        )[:8],
        "trend": [{"date": d, "count": trend_map[d]} for d in sorted(trend_map.keys())],
        "mastered_pie": [
            {"name": "未掌握", "value": unmastered},
            {"name": "已掌握", "value": mastered},
        ],
    }


def build_class_weak_kps(
    db: Session,
    course_id: int,
    *,
    student_ids: list[int] | None = None,
    limit: int = 8,
) -> list[tuple[int, str, int, int]]:
    if student_ids is None:
        student_ids = _enrolled_student_ids(db, course_id)
    if not student_ids:
        return []

    for uid in student_ids:
        refresh_user_mastery(db, user_id=uid, kp_id=None)

    kp_rows = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.course_id == course_id, KnowledgePoint.deleted == 0)
        .all()
    )
    if not kp_rows:
        return []

    kp_ids = [kp.id for kp in kp_rows]
    kp_name_map = {kp.id: kp.name for kp in kp_rows}

    mastery_rows = (
        db.query(UserKpMastery)
        .filter(
            UserKpMastery.user_id.in_(student_ids),
            UserKpMastery.kp_id.in_(kp_ids),
            UserKpMastery.deleted == 0,
        )
        .all()
    )

    scores_by_kp: dict[int, list[int]] = defaultdict(list)
    for row in mastery_rows:
        scores_by_kp[row.kp_id].append(row.score)

    averaged: list[tuple[int, str, int, int]] = []
    for kp_id, scores in scores_by_kp.items():
        avg = round(sum(scores) / len(scores))
        averaged.append((kp_id, kp_name_map[kp_id], avg, course_id))

    averaged.sort(key=lambda x: x[2])
    return averaged[:limit]


def build_event_trend(
    db: Session,
    course_id: int,
    *,
    student_ids: list[int] | None = None,
    days: int = 7,
) -> list[dict[str, Any]]:
    if student_ids is None:
        student_ids = _enrolled_student_ids(db, course_id)

    today = date.today()
    start = today - timedelta(days=days - 1)
    trend_map: dict[str, int] = {
        (start + timedelta(days=i)).isoformat(): 0 for i in range(days)
    }

    if not student_ids:
        return [{"date": d, "count": trend_map[d]} for d in sorted(trend_map.keys())]

    since = datetime.combine(start, datetime.min.time())
    rows = (
        db.query(LearningEvent)
        .filter(
            LearningEvent.course_id == course_id,
            LearningEvent.user_id.in_(student_ids),
            LearningEvent.deleted == 0,
            LearningEvent.created_at >= since,
        )
        .all()
    )
    for row in rows:
        if row.created_at:
            day_key = row.created_at.date().isoformat()
            if day_key in trend_map:
                trend_map[day_key] += 1

    return [{"date": d, "count": trend_map[d]} for d in sorted(trend_map.keys())]


def count_active_students_7d(
    db: Session,
    course_id: int,
    *,
    student_ids: list[int] | None = None,
) -> int:
    if student_ids is None:
        student_ids = _enrolled_student_ids(db, course_id)
    if not student_ids:
        return 0

    since = datetime.now() - timedelta(days=7)
    active_ids = {
        row[0]
        for row in db.query(LearningEvent.user_id)
        .filter(
            LearningEvent.course_id == course_id,
            LearningEvent.user_id.in_(student_ids),
            LearningEvent.deleted == 0,
            LearningEvent.created_at >= since,
        )
        .distinct()
        .all()
    }
    return len(active_ids)


def count_events_7d_for_course(
    db: Session,
    course_id: int,
    *,
    student_ids: list[int] | None = None,
) -> int:
    if student_ids is None:
        student_ids = _enrolled_student_ids(db, course_id)
    if not student_ids:
        return 0

    since = datetime.now() - timedelta(days=7)
    return (
        db.query(LearningEvent)
        .filter(
            LearningEvent.course_id == course_id,
            LearningEvent.user_id.in_(student_ids),
            LearningEvent.deleted == 0,
            LearningEvent.created_at >= since,
        )
        .count()
    )


def build_teacher_course_overview(
    db: Session,
    course: Course,
    *,
    days: int = 7,
) -> dict[str, Any]:
    student_ids = _enrolled_student_ids(db, course.id)
    wrong_stats = build_class_wrong_book_stats(
        db, course.id, student_ids=student_ids, days=days
    )
    weak = build_class_weak_kps(db, course.id, student_ids=student_ids)
    event_trend = build_event_trend(db, course.id, student_ids=student_ids, days=days)

    students = load_enrolled_students(db, course.id)
    wrong_summary = wrong_stats["summary"]
    return {
        "course": {
            "id": course.id,
            "name": course.name,
            "teacher_id": course.teacher_id,
            "teacher_name": _get_teacher_name(db, course.teacher_id),
        },
        "students": students,
        "summary": {
            "student_count": len(student_ids),
            "active_students_7d": count_active_students_7d(
                db, course.id, student_ids=student_ids
            ),
            "total_events_7d": count_events_7d_for_course(
                db, course.id, student_ids=student_ids
            ),
            "wrong_total": wrong_summary["total"],
            "wrong_unmastered": wrong_summary["unmastered"],
            "mastery_rate": wrong_summary["mastery_rate"],
        },
        "wrong_book_stats": wrong_stats,
        "weak_kps": [
            {"kp_id": k, "name": n, "score": s, "course_id": c} for k, n, s, c in weak
        ],
        "event_trend": event_trend,
    }
