from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.chat import DEFAULT_SESSION_TITLE, summarize_session_title
from app.services.llm_service import build_rag_prompt
from app.services.vector_store import VectorHit
from tests.conftest import login


def test_build_rag_prompt_no_hits():
    messages = build_rag_prompt([], "什么是变量?")
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert "暂无相关资料" in messages[-1]["content"]


def test_build_rag_prompt_with_hits():
    hits = [
        VectorHit(chunk_id=1, course_id=1, text="Python 变量", page=2, score=0.9),
    ]
    messages = build_rag_prompt(hits, "什么是变量?")
    assert "chunk_id=1" in messages[-1]["content"]


def test_build_rag_prompt_injects_course_code_language():
    messages = build_rag_prompt(
        [],
        "二分查找怎么写?",
        code_language="C++",
        code_fence_tag="cpp",
    )
    system = messages[0]["content"]
    assert "C++" in system
    assert "```cpp" in system


def test_build_rag_prompt_with_history():
    history = [
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "你好小明"},
    ]
    messages = build_rag_prompt([], "你还记得我吗?", history=history)
    assert len(messages) == 4
    assert messages[1]["content"] == "我叫小明"
    assert messages[2]["content"] == "你好小明"
    assert "你还记得我吗" in messages[3]["content"]


def test_summarize_session_title():
    assert summarize_session_title("python for循环怎么写") == "python for"
    assert summarize_session_title("  你好  \n世界  ") == "你好 世界"
    assert summarize_session_title("短") == "短"


@pytest.mark.asyncio
async def test_chat_unenrolled_student_forbidden(client, seed_users, seed_course):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"course_id": seed_course.id, "title": "test"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_chat_with_mock_llm(client, db_session, seed_users, seed_course):
    from app.models.course import CourseStudent

    student = seed_users["student"]
    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch("app.api.v1.chat.retrieve_chunks", new=AsyncMock(return_value=[])):

        async def fake_stream(_messages):
            from app.services.llm_service import LlmStreamChunk

            yield LlmStreamChunk("content", "你")
            yield LlmStreamChunk("content", "好")

        with patch("app.api.v1.chat.stream_llm", side_effect=fake_stream):
            create = await client.post(
                "/api/v1/chat/sessions",
                headers=headers,
                json={"course_id": seed_course.id},
            )
            session_id = create.json()["data"]["id"]

            resp = await client.post(
                f"/api/v1/chat/sessions/{session_id}/messages",
                headers=headers,
                json={"content": "什么是 Python?"},
            )
            assert resp.status_code == 200
            assert "event: message" in resp.text

            history = await client.get(
                f"/api/v1/chat/sessions/{session_id}/messages",
                headers=headers,
            )
            data = history.json()["data"]
            assert len(data) == 2
            assert data[0]["role"] == "user"
            assert data[0]["content"] == "什么是 Python?"
            assert data[1]["role"] == "assistant"
            assert data[1]["content"] == "你好"

            sessions = await client.get(
                f"/api/v1/chat/sessions?course_id={seed_course.id}",
                headers=headers,
            )
            session_row = next(
                s for s in sessions.json()["data"] if s["id"] == session_id
            )
            assert session_row["title"] == summarize_session_title("什么是 Python?")

            captured_messages: list[list] = []

            async def fake_stream_with_capture(msgs):
                captured_messages.append(msgs)
                from app.services.llm_service import LlmStreamChunk

                yield LlmStreamChunk("content", "记得，你问了 Python")

            with patch("app.api.v1.chat.stream_llm", side_effect=fake_stream_with_capture):
                resp2 = await client.post(
                    f"/api/v1/chat/sessions/{session_id}/messages",
                    headers=headers,
                    json={"content": "你还记得我刚才问了什么吗"},
                )
                assert resp2.status_code == 200
                assert len(captured_messages) == 1
                llm_msgs = captured_messages[0]
                assert any("Python" in m.get("content", "") for m in llm_msgs)
                assert any("你还记得" in m.get("content", "") for m in llm_msgs)


@pytest.mark.asyncio
async def test_delete_session(client, db_session, seed_users, seed_course):
    from app.models.chat import ChatMessage, ChatSession

    student = seed_users["student"]
    from app.models.course import CourseStudent

    db_session.add(CourseStudent(course_id=seed_course.id, user_id=student.id))
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create = await client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"course_id": seed_course.id},
    )
    session_id = create.json()["data"]["id"]

    resp = await client.delete(
        f"/api/v1/chat/sessions/{session_id}",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["code"] == 0

    session = db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
    assert session.deleted == 1

    messages = (
        db_session.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .all()
    )
    assert all(m.deleted == 1 for m in messages)

    list_resp = await client.get(
        f"/api/v1/chat/sessions?course_id={seed_course.id}",
        headers=headers,
    )
    ids = [s["id"] for s in list_resp.json()["data"]]
    assert session_id not in ids
