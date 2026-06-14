from datetime import date, datetime, timedelta

from app.models.learning import WrongQuestionBook, WrongQuestionSourceType
from app.services.wrong_book_analysis import build_wrong_book_stats


def test_trend_includes_today(db_session, seed_users, seed_course):
    student = seed_users["student"]
    today = date.today()
    db_session.add(
        WrongQuestionBook(
            user_id=student.id,
            course_id=seed_course.id,
            source_type=WrongQuestionSourceType.chat_message,
            ref_id=90001,
            kp_id=None,
            mastered=False,
            created_at=datetime.combine(today, datetime.min.time()),
        )
    )
    db_session.commit()

    stats = build_wrong_book_stats(db_session, student.id, course_id=seed_course.id, days=7)
    assert len(stats["trend"]) == 7
    assert stats["trend"][-1]["date"] == today.isoformat()
    assert stats["trend"][-1]["count"] >= 1
