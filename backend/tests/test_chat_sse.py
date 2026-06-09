from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import login


@pytest.mark.asyncio
async def test_sse_stream_format(client, db_session, seed_users, seed_course):
    from app.models.course import CourseStudent

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create = await client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"course_id": seed_course.id, "title": "sse"},
    )
    session_id = create.json()["data"]["id"]

    async def fake_stream(_messages):
        from app.services.llm_service import LlmStreamChunk

        yield LlmStreamChunk("content", "你")
        yield LlmStreamChunk("content", "好")

    with patch("app.api.v1.chat.retrieve_chunks", new=AsyncMock(return_value=[])), patch(
        "app.api.v1.chat.stream_llm", side_effect=fake_stream
    ):
        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"content": "hi"},
        )

    body = resp.text
    assert 'data: {"delta": "你"' in body or '"delta": "你"' in body
    assert '"done": true' in body.lower() or '"done": True' in body
