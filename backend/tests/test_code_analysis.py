from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import get_settings
from app.core.exceptions import BusinessException, ERR_RATE_LIMIT
from app.core.rate_limit import check_llm_rate_limit
from app.core.security import get_redis
from app.models.code import CodeLanguage
from app.schemas.code_analysis import AnalysisResultData
from app.services.code_analysis import (
    build_analysis_messages,
    demo_analysis_result,
    parse_analysis_result,
    prepare_source_code,
    validate_language,
)
from tests.conftest import login

MOCK_JSON = """
{
  "summary": "存在缩进问题",
  "levels": {
    "syntax": {
      "score": "error",
      "issues": [{"line": 2, "message": "缩进错误", "hint": "对齐 elif"}],
      "suggestions": ["检查缩进"]
    },
    "semantic": {"score": "ok", "issues": [], "suggestions": []},
    "runtime": {"score": "warning", "issues": [], "stderr_hint": null}
  },
  "fixed_code": "print('ok')",
  "examples": ["示例"]
}
"""


def test_validate_language_all_supported():
    for lang in ("c", "cpp", "python", "java"):
        assert validate_language(lang).value == lang
    assert validate_language("c++").value == "cpp"
    with pytest.raises(ValueError):
        validate_language("rust")


def test_prepare_source_code_truncation():
    get_settings.cache_clear()
    settings = get_settings()
    long_code = "x" * (settings.code_max_source_chars + 100)
    prepared, truncated = prepare_source_code(long_code)
    assert truncated
    assert len(prepared) == settings.code_max_source_chars


def test_parse_analysis_result():
    result = parse_analysis_result(MOCK_JSON)
    assert result.summary == "存在缩进问题"
    assert result.levels.syntax.score == "error"


def test_build_analysis_messages():
    messages = build_analysis_messages("python", "print(1)", False)
    assert messages[0]["role"] == "system"
    assert "print(1)" in messages[1]["content"]


def test_demo_analysis_result():
    code = "while True:\n    pass\n"
    result = demo_analysis_result("python", code, False)
    assert result.levels.semantic.score == "warning"


@pytest.mark.asyncio
async def test_submit_without_enrollment(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value=MOCK_JSON),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={
                "language": "python",
                "source_code": "print(1)",
            },
        )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["submission"]["course_id"] is None


@pytest.mark.asyncio
async def test_submit_java_language(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value=MOCK_JSON),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={
                "language": "java",
                "source_code": "class Main {}",
            },
        )
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_submit_invalid_language(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post(
        "/api/v1/code/submit",
        headers=headers,
        json={
            "language": "rust",
            "source_code": "print(1)",
        },
    )
    assert resp.json()["code"] == 40001


@pytest.mark.asyncio
async def test_submit_empty_source_rejected(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post(
        "/api/v1/code/submit",
        headers=headers,
        json={
            "language": "python",
            "source_code": "",
        },
    )
    assert resp.json()["code"] == 40001


@pytest.mark.asyncio
async def test_submit_with_mock_llm(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value=MOCK_JSON),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={
                "language": "python",
                "source_code": "if True:\nprint(1)",
            },
        )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["analysis"]["status"] == "done"
    assert body["data"]["analysis"]["result"]["summary"] == "存在缩进问题"
    submission_id = body["data"]["submission"]["id"]

    get_resp = await client.get(
        f"/api/v1/code/submit/{submission_id}/result",
        headers=headers,
    )
    assert get_resp.json()["data"]["submission"]["id"] == submission_id


@pytest.mark.asyncio
async def test_submit_llm_dirty_json_failed(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value="not json"),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={
                "language": "python",
                "source_code": "print(1)",
            },
        )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["analysis"]["status"] == "failed"


@pytest.mark.asyncio
async def test_submit_dangerous_input(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    with patch(
        "app.services.code_analysis.invoke_llm",
        new=AsyncMock(return_value=MOCK_JSON),
    ):
        resp = await client.post(
            "/api/v1/code/submit",
            headers=headers,
            json={
                "language": "python",
                "source_code": "eval('1')",
            },
        )
    body = resp.json()
    assert body["data"]["analysis"]["status"] == "failed"


@pytest.mark.asyncio
async def test_list_submissions_empty(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        "/api/v1/code/submissions?page_num=1&page_size=20",
        headers=headers,
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 0
    assert body["data"]["list"] == []


@pytest.mark.asyncio
async def test_list_submissions_with_bad_result_json(client, db_session, seed_users):
    from app.models.code import AnalysisResult, AnalysisStatus, CodeSubmission

    student = seed_users["student"]
    sub = CodeSubmission(
        user_id=student.id,
        course_id=None,
        language=CodeLanguage.python,
        source_code="print(1)",
        version=1,
    )
    db_session.add(sub)
    db_session.flush()
    db_session.add(
        AnalysisResult(
            submission_id=sub.id,
            status=AnalysisStatus.done,
            result_json=["invalid-list"],
        )
    )
    db_session.commit()

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get(
        "/api/v1/code/submissions?page_num=1&page_size=20",
        headers=headers,
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["list"][0]["summary"] is None
    assert body["data"]["list"][0]["status"] == "done"


@pytest.mark.asyncio
async def test_rate_limit(client, db_session, seed_users):
    student = seed_users["student"]

    get_settings.cache_clear()
    settings = get_settings()
    redis = get_redis()
    redis.set(f"rate:llm:{student.id}", str(settings.llm_daily_limit))

    with pytest.raises(BusinessException) as exc_info:
        check_llm_rate_limit(student.id)
    assert exc_info.value.code == ERR_RATE_LIMIT
