from datetime import datetime, timedelta

import pytest

from app.models.course import CourseStudent
from app.models.learning import (
    KnowledgePoint,
    LearningEvent,
    LearningEventType,
    WrongQuestionBook,
    WrongQuestionSourceType,
)
from tests.conftest import login


@pytest.fixture
def enrolled_student(db_session, seed_course, seed_users):
    db_session.add(
        CourseStudent(course_id=seed_course.id, user_id=seed_users["student"].id)
    )
    db_session.commit()
    return seed_users["student"]


@pytest.fixture
def seed_class_data(db_session, seed_course, enrolled_student, seed_kp):
    student = enrolled_student
    now = datetime.now()

    for i in range(3):
        created_at = now - timedelta(days=i, hours=2)
        db_session.add(
            WrongQuestionBook(
                user_id=student.id,
                course_id=seed_course.id,
                source_type=WrongQuestionSourceType.code_submission,
                ref_id=100 + i,
                kp_id=seed_kp.id,
                mastered=i == 2,
                created_at=created_at,
            )
        )
        db_session.add(
            LearningEvent(
                user_id=student.id,
                course_id=seed_course.id,
                event_type=LearningEventType.code_submit,
                kp_id=seed_kp.id,
                created_at=created_at,
            )
        )

    db_session.commit()
    return seed_course


@pytest.mark.asyncio
async def test_teacher_overview_success(
    client, seed_class_data, seed_users, seed_kp
):
    tokens = await login(client, seed_users["teacher"].username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_class_data.id}/overview",
        headers=headers,
        params={"days": 7},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]

    assert data["course"]["id"] == seed_class_data.id
    assert data["course"]["teacher_name"] == seed_users["teacher"].username
    assert data["summary"]["student_count"] == 1
    assert len(data["students"]) == 1
    assert data["students"][0]["username"] == seed_users["student"].username
    assert data["students"][0]["wrong_count"] == 3
    assert data["students"][0]["unmastered_count"] == 2
    assert data["summary"]["active_students_7d"] == 1
    assert data["summary"]["wrong_total"] == 3
    assert data["summary"]["wrong_unmastered"] == 2
    assert data["wrong_book_stats"]["summary"]["total"] == 3
    assert data["wrong_book_stats"]["summary"]["unmastered"] == 2
    assert len(data["wrong_book_stats"]["trend"]) == 7
    assert len(data["event_trend"]) == 7
    assert data["summary"]["total_events_7d"] >= 3

    weak_ids = {item["kp_id"] for item in data["weak_kps"]}
    assert seed_kp.id in weak_ids


@pytest.mark.asyncio
async def test_teacher_overview_admin(client, seed_class_data, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_class_data.id}/overview",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_teacher_overview_student_forbidden(
    client, seed_class_data, seed_users
):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_class_data.id}/overview",
        headers=headers,
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_teacher_overview_other_teacher_forbidden(
    client, db_session, seed_class_data, seed_users
):
    from app.core.security import hash_password
    from app.models.user import User, UserRole, UserStatus

    other = User(
        username="other_teacher",
        password_hash=hash_password("Teacher123!"),
        role=UserRole.teacher,
        status=UserStatus.active,
    )
    db_session.add(other)
    db_session.commit()

    tokens = await login(client, other.username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_class_data.id}/overview",
        headers=headers,
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_teacher_overview_empty_class(client, seed_course, seed_users):
    tokens = await login(client, seed_users["teacher"].username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_course.id}/overview",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["summary"]["student_count"] == 0
    assert data["summary"]["wrong_total"] == 0
    assert data["weak_kps"] == []


@pytest.mark.asyncio
async def test_teacher_overview_aggregates_all_students(
    client, db_session, seed_course, seed_users, seed_kp
):
    from app.core.security import hash_password
    from app.models.user import User, UserRole, UserStatus

    student2 = User(
        username="student2",
        password_hash=hash_password("Student123!"),
        role=UserRole.student,
        status=UserStatus.active,
    )
    db_session.add(student2)
    db_session.flush()

    for uid in (seed_users["student"].id, student2.id):
        db_session.add(CourseStudent(course_id=seed_course.id, user_id=uid))
        db_session.add(
            WrongQuestionBook(
                user_id=uid,
                course_id=seed_course.id,
                source_type=WrongQuestionSourceType.code_submission,
                ref_id=uid * 10,
                kp_id=seed_kp.id,
                mastered=False,
            )
        )
    db_session.commit()

    tokens = await login(client, seed_users["teacher"].username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/teacher/courses/{seed_course.id}/overview",
        headers=headers,
    )
    data = resp.json()["data"]
    assert data["summary"]["student_count"] == 2
    assert len(data["students"]) == 2
    assert data["summary"]["wrong_total"] == 2
    assert data["wrong_book_stats"]["summary"]["total"] == 2


@pytest.fixture
def seed_kp(db_session, seed_course):
    kp = KnowledgePoint(
        course_id=seed_course.id,
        name="代码基础",
        sort_order=1,
    )
    db_session.add(kp)
    db_session.commit()
    db_session.refresh(kp)
    return kp
