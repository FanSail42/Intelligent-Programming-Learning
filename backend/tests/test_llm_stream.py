import pytest

from app.services.llm_service import LlmStreamChunk, _chunks_from_stream_payload
from tests.conftest import login


def test_chunks_from_empty_choices():
    assert _chunks_from_stream_payload({"choices": []}) == []


def test_chunks_from_missing_choices():
    assert _chunks_from_stream_payload({"id": "chunk-1"}) == []


def test_chunks_from_content_delta():
    parts = _chunks_from_stream_payload(
        {"choices": [{"delta": {"content": "你好"}}]}
    )
    assert parts == [LlmStreamChunk("content", "你好")]


def test_chunks_from_reasoning_delta():
    parts = _chunks_from_stream_payload(
        {"choices": [{"delta": {"reasoning_content": "思考中"}}]}
    )
    assert parts == [LlmStreamChunk("reasoning", "思考中")]


@pytest.mark.asyncio
async def test_chat_sse_with_empty_choices_in_stream(client, db_session, seed_users, seed_course):
    """Regression: some LLM APIs emit choices=[] heartbeats during thinking streams."""
    from unittest.mock import AsyncMock, patch

    from app.models.course import CourseStudent

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create = await client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"course_id": seed_course.id, "title": "empty-choices"},
    )
    session_id = create.json()["data"]["id"]

    async def fake_stream(_messages):
        from app.services.llm_service import LlmStreamChunk

        yield LlmStreamChunk("reasoning", "分析")
        yield LlmStreamChunk("content", "基本语法包括变量与语句。")

    with patch("app.api.v1.chat.retrieve_chunks", new=AsyncMock(return_value=[])), patch(
        "app.api.v1.chat.stream_llm", side_effect=fake_stream
    ):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"content": "基本语法"},
        )

    body = resp.text
    assert "list index out of range" not in body
    assert "基本语法" in body or "变量" in body
    assert '"done": true' in body.lower() or '"done": True' in body
