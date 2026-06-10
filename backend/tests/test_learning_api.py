from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.code import AnalysisResult, AnalysisStatus, CodeLanguage, CodeSubmission
from app.models.learning import KnowledgePoint, WrongQuestionBook, WrongQuestionSourceType
from tests.conftest import login

MOCK_JSON_ERROR = """
{
  "summary": "语义有问题",
  "levels": {
    "syntax": {"score": "ok", "issues": [], "suggestions": []},
    "semantic": {"score": "error", "issues": [{"message": "死循环", "explanation": "条件错误"}], "suggestions": []},
    "runtime": {"score": "ok", "issues": [], "stderr_hint": null}
  },
  "fixed_code": null,
  "examples": []
}
"""


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


@pytest.mark.asyncio
async def test_code_submit_creates_wrong_book(client, db_session, seed_users, seed_kp):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value=MOCK_JSON_ERROR),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={"language": "python", "source_code": "while True: pass"},
        )
    assert resp.json()["code"] == 0
    submission_id = resp.json()["data"]["submission"]["id"]

    wrong = (
        db_session.query(WrongQuestionBook)
        .filter(
            WrongQuestionBook.user_id == seed_users["student"].id,
            WrongQuestionBook.source_type == WrongQuestionSourceType.code_submission,
            WrongQuestionBook.ref_id == submission_id,
        )
        .first()
    )
    assert wrong is not None
    assert wrong.mastered is False


@pytest.mark.asyncio
async def test_dashboard(client, db_session, seed_users, seed_kp):
    student = seed_users["student"]
    db_session.add(
        WrongQuestionBook(
            user_id=student.id,
            course_id=seed_kp.course_id,
            source_type=WrongQuestionSourceType.code_submission,
            ref_id=1,
            kp_id=seed_kp.id,
            mastered=False,
        )
    )
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/learning/dashboard", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["summary"]["wrong_count"] >= 1


@pytest.mark.asyncio
async def test_dashboard_with_course_id(client, db_session, seed_users, seed_course, seed_kp):
    from app.models.course import CourseStudent
    from app.models.learning import UserKpMastery

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.add(UserKpMastery(user_id=student.id, kp_id=seed_kp.id, score=55))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/learning/dashboard",
        headers=headers,
        params={"course_id": seed_course.id},
    )
    assert resp.status_code == 200
    weak = resp.json()["data"]["weak_kps"]
    assert len(weak) >= 1
    assert any(w["kp_id"] == seed_kp.id for w in weak)


@pytest.mark.asyncio
async def test_wrong_book_list_and_mastered(client, db_session, seed_users, seed_kp):
    student = seed_users["student"]
    row = WrongQuestionBook(
        user_id=student.id,
        course_id=seed_kp.course_id,
        source_type=WrongQuestionSourceType.code_submission,
        ref_id=99,
        kp_id=seed_kp.id,
        mastered=False,
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    list_resp = await client.get("/api/v1/learning/wrong-book", headers=headers)
    assert list_resp.json()["data"]["total"] >= 1

    put_resp = await client.put(
        f"/api/v1/learning/wrong-book/{row.id}/mastered",
        headers=headers,
        json={"mastered": True},
    )
    assert put_resp.json()["code"] == 0
    assert put_resp.json()["data"]["mastered"] is True


@pytest.mark.asyncio
async def test_recommendations_requires_enrollment(client, seed_users, seed_course):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        f"/api/v1/learning/recommendations?course_id={seed_course.id}",
        headers=headers,
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_recommendations_enrolled(client, db_session, seed_users, seed_course, seed_kp):
    from app.models.course import CourseStudent

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        f"/api/v1/learning/recommendations?course_id={seed_course.id}",
        headers=headers,
    )
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    if body["data"]:
        item = body["data"][0]
        assert "action_type" in item
        assert "priority" in item
        assert "score" in item


@pytest.mark.asyncio
async def test_wrong_book_stats(client, db_session, seed_users, seed_kp):
    from app.models.code import AnalysisResult, AnalysisStatus, CodeLanguage, CodeSubmission

    student = seed_users["student"]
    sub = CodeSubmission(
        user_id=student.id,
        language=CodeLanguage.python,
        source_code="while True: pass",
        version=1,
    )
    db_session.add(sub)
    db_session.flush()
    db_session.add(
        AnalysisResult(
            submission_id=sub.id,
            status=AnalysisStatus.done,
            result_json={
                "summary": "语义有问题",
                "levels": {
                    "syntax": {"score": "ok", "issues": [], "suggestions": []},
                    "semantic": {
                        "score": "error",
                        "issues": [{"message": "死循环"}],
                        "suggestions": ["修正循环条件"],
                    },
                    "runtime": {"score": "ok", "issues": [], "suggestions": []},
                },
            },
        )
    )
    db_session.add(
        WrongQuestionBook(
            user_id=student.id,
            course_id=seed_kp.course_id,
            source_type=WrongQuestionSourceType.code_submission,
            ref_id=sub.id,
            kp_id=seed_kp.id,
            mastered=False,
        )
    )
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    stats_resp = await client.get("/api/v1/learning/wrong-book/stats", headers=headers)
    stats = stats_resp.json()["data"]
    assert stats["summary"]["total"] >= 1
    assert len(stats["by_source"]) == 2
    assert {item["source_type"] for item in stats["by_source"]} == {
        "code_submission",
        "chat_message",
    }
    assert any(c["category"] == "semantic_error" for c in stats["by_category"])

    list_resp = await client.get(
        "/api/v1/learning/wrong-book",
        headers=headers,
        params={"category": "semantic_error"},
    )
    body = list_resp.json()["data"]
    assert body["total"] >= 1
    item = body["list"][0]
    assert item["category"] == "semantic_error"
    assert item["category_label"] == "语义与逻辑"
    assert len(item["issues"]) >= 1


@pytest.mark.asyncio
async def test_wrong_book_stats_course_filter_null_course_id(
    client, db_session, seed_users, seed_kp
):
    """Rows with course_id=NULL but kp on course should appear under course filter."""
    from app.models.code import CodeLanguage, CodeSubmission

    student = seed_users["student"]
    sub = CodeSubmission(
        user_id=student.id,
        language=CodeLanguage.cpp,
        source_code="int main(){ while(1){} }",
        version=1,
    )
    db_session.add(sub)
    db_session.flush()
    db_session.add(
        WrongQuestionBook(
            user_id=student.id,
            course_id=None,
            source_type=WrongQuestionSourceType.code_submission,
            ref_id=sub.id,
            kp_id=seed_kp.id,
            mastered=False,
        )
    )
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    stats_resp = await client.get(
        "/api/v1/learning/wrong-book/stats",
        headers=headers,
        params={"course_id": seed_kp.course_id},
    )
    stats = stats_resp.json()["data"]
    assert stats["summary"]["total"] >= 1


@pytest.mark.asyncio
async def test_recommendations_prefers_wrong_book(client, db_session, seed_users, seed_course, seed_kp):
    from app.models.course import CourseStudent
    from app.models.learning import WrongQuestionBook, WrongQuestionSourceType

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.add(
        WrongQuestionBook(
            user_id=student.id,
            course_id=seed_course.id,
            source_type=WrongQuestionSourceType.code_submission,
            ref_id=101,
            kp_id=seed_kp.id,
            mastered=False,
        )
    )
    from app.models.learning import UserKpMastery

    db_session.add(UserKpMastery(user_id=student.id, kp_id=seed_kp.id, score=45))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        f"/api/v1/learning/recommendations?course_id={seed_course.id}",
        headers=headers,
    )
    data = resp.json()["data"]
    assert data[0]["action_type"] == "review_wrong_book"
    assert data[0]["wrong_count"] >= 1
