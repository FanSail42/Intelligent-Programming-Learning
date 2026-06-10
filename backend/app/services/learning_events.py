from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.code import AnalysisResult, AnalysisStatus, CodeSubmission
from app.models.learning import (
    KnowledgePoint,
    LearningEvent,
    LearningEventType,
    WrongQuestionBook,
    WrongQuestionSourceType,
)
from app.services.code_helpers import validate_result_data
from app.services.learning_cache import clear_dashboard_cache
from app.services.mastery import refresh_user_mastery


def record_event(
    db: Session,
    *,
    user_id: int,
    event_type: LearningEventType | str,
    course_id: int | None = None,
    kp_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> LearningEvent:
    if isinstance(event_type, str):
        event_type = LearningEventType(event_type)
    event = LearningEvent(
        user_id=user_id,
        course_id=course_id,
        event_type=event_type,
        kp_id=kp_id,
        payload_json=payload,
    )
    db.add(event)
    db.flush()
    clear_dashboard_cache(user_id)
    return event


def upsert_wrong_question(
    db: Session,
    *,
    user_id: int,
    source_type: WrongQuestionSourceType | str,
    ref_id: int,
    course_id: int | None = None,
    kp_id: int | None = None,
) -> WrongQuestionBook | None:
    if isinstance(source_type, str):
        source_type = WrongQuestionSourceType(source_type)
    existing = (
        db.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == user_id,
            WrongQuestionBook.source_type == source_type,
            WrongQuestionBook.ref_id == ref_id,
            WrongQuestionBook.deleted == 0,
        )
        .first()
    )
    if existing:
        return existing
    row = WrongQuestionBook(
        user_id=user_id,
        course_id=course_id,
        source_type=source_type,
        ref_id=ref_id,
        kp_id=kp_id,
        mastered=False,
    )
    db.add(row)
    db.flush()
    clear_dashboard_cache(user_id)
    refresh_user_mastery(db, user_id=user_id, kp_id=kp_id)
    return row


def _analysis_has_serious_issue(result_json: dict | None) -> bool:
    data = validate_result_data(result_json)
    if not data:
        return False
    return (
        data.levels.semantic.score == "error"
        or data.levels.runtime.score == "error"
        or data.levels.syntax.score == "error"
    )


def resolve_default_kp(db: Session, user_id: int) -> KnowledgePoint | None:
    """Prefer 代码基础 KP from enrolled courses so wrong-book links to the right course."""
    from app.models.course import CourseStudent

    enrolled_ids = [
        row[0]
        for row in db.query(CourseStudent.course_id)
        .filter(CourseStudent.user_id == user_id, CourseStudent.deleted == 0)
        .all()
    ]
    if enrolled_ids:
        kp = (
            db.query(KnowledgePoint)
            .filter(
                KnowledgePoint.name == "代码基础",
                KnowledgePoint.course_id.in_(enrolled_ids),
                KnowledgePoint.deleted == 0,
            )
            .order_by(KnowledgePoint.id.asc())
            .first()
        )
        if kp:
            return kp
    return (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.name == "代码基础", KnowledgePoint.deleted == 0)
        .order_by(KnowledgePoint.id.asc())
        .first()
    )


def after_code_submission(
    db: Session,
    *,
    user_id: int,
    submission: CodeSubmission,
    analysis: AnalysisResult,
    default_kp_id: int | None = None,
) -> None:
    record_event(
        db,
        user_id=user_id,
        event_type=LearningEventType.code_submit,
        course_id=submission.course_id,
        kp_id=default_kp_id,
        payload={
            "submission_id": submission.id,
            "language": submission.language.value if hasattr(submission.language, "value") else submission.language,
        },
    )

    need_wrong = analysis.status == AnalysisStatus.failed or _analysis_has_serious_issue(
        analysis.result_json
    )
    if need_wrong:
        effective_course_id = submission.course_id
        if effective_course_id is None and default_kp_id is not None:
            kp = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.id == default_kp_id, KnowledgePoint.deleted == 0)
                .first()
            )
            if kp:
                effective_course_id = kp.course_id

        record_event(
            db,
            user_id=user_id,
            event_type=LearningEventType.code_analysis_error,
            course_id=effective_course_id,
            kp_id=default_kp_id,
            payload={"submission_id": submission.id},
        )
        upsert_wrong_question(
            db,
            user_id=user_id,
            source_type=WrongQuestionSourceType.code_submission,
            ref_id=submission.id,
            course_id=effective_course_id,
            kp_id=default_kp_id,
        )


def after_chat_no_context(
    db: Session,
    *,
    user_id: int,
    course_id: int,
    session_id: int,
    message_id: int,
    kp_id: int | None = None,
) -> None:
    record_event(
        db,
        user_id=user_id,
        event_type=LearningEventType.chat_no_context,
        course_id=course_id,
        kp_id=kp_id,
        payload={"session_id": session_id, "message_id": message_id},
    )
    upsert_wrong_question(
        db,
        user_id=user_id,
        source_type=WrongQuestionSourceType.chat_message,
        ref_id=message_id,
        course_id=course_id,
        kp_id=kp_id,
    )


def count_events_7d(db: Session, user_id: int) -> int:
    since = datetime.now() - timedelta(days=7)
    return (
        db.query(LearningEvent)
        .filter(
            LearningEvent.user_id == user_id,
            LearningEvent.deleted == 0,
            LearningEvent.created_at >= since,
        )
        .count()
    )
