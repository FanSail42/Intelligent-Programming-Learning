import pytest

from app.core.secret_crypto import decrypt_secret, encrypt_secret
from app.services.ai_usage import record_llm_usage
from tests.conftest import login


@pytest.mark.asyncio
async def test_admin_list_ai_models(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/ai/models", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["provider"] == "阿里云百炼"
    assert any(m["id"] == "qwen3.6-flash" for m in body["data"]["chat_models"])
    assert "bailian.console.aliyun.com" in body["data"]["console_url"]


@pytest.mark.asyncio
async def test_admin_get_ai_config(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/ai/config", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["llm_model"]
    assert "llm_daily_limit" in body["data"]


@pytest.mark.asyncio
async def test_admin_update_ai_config(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.put(
        "/api/v1/admin/ai/config",
        headers=headers,
        json={
            "llm_model": "qwen-plus",
            "llm_api_key": "sk-test-key-12345678",
            "llm_daily_limit": 50,
        },
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["llm_model"] == "qwen-plus"
    assert body["data"]["llm_daily_limit"] == 50
    assert body["data"]["llm_api_key_configured"] is True
    assert "****" in body["data"]["llm_api_key_masked"]

    get_resp = await client.get("/api/v1/admin/ai/config", headers=headers)
    assert get_resp.json()["data"]["llm_model"] == "qwen-plus"


@pytest.mark.asyncio
async def test_admin_add_custom_model_and_use(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    add_resp = await client.post(
        "/api/v1/admin/ai/models/custom",
        headers=headers,
        json={"id": "kimi-k2.6", "name": "Kimi K2.6", "description": "新模型测试"},
    )
    assert add_resp.json()["code"] == 0
    assert add_resp.json()["data"]["id"] == "kimi-k2.6"

    models_resp = await client.get("/api/v1/admin/ai/models", headers=headers)
    ids = {m["id"] for m in models_resp.json()["data"]["chat_models"]}
    assert "kimi-k2.6" in ids

    upd_resp = await client.put(
        "/api/v1/admin/ai/config",
        headers=headers,
        json={"llm_model": "kimi-k2.6"},
    )
    assert upd_resp.json()["code"] == 0
    assert upd_resp.json()["data"]["llm_model"] == "kimi-k2.6"

    del_resp = await client.delete(
        "/api/v1/admin/ai/models/custom/kimi-k2.6",
        headers=headers,
    )
    assert del_resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_admin_update_invalid_model(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.put(
        "/api/v1/admin/ai/config",
        headers=headers,
        json={"llm_model": "unknown-model"},
    )
    assert resp.json()["code"] == 40001


@pytest.mark.asyncio
async def test_admin_student_token_usage(client, seed_users):
    student_id = seed_users["student"].id
    record_llm_usage(user_id=student_id, tokens=300, scene="chat_rag", model="qwen-plus")
    record_llm_usage(user_id=student_id, tokens=150, scene="code_analysis", model="qwen-plus")

    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/admin/ai/usage/students",
        headers=headers,
        params={"username": "student"},
    )
    body = resp.json()
    assert body["code"] == 0
    row = body["data"]["list"][0]
    assert row["username"] == "student"
    assert row["tokens_today"] >= 450
    assert row["calls_today"] >= 2
    assert row["last_model_id"] == "qwen-plus"
    assert len(row["models_today"]) >= 1
    assert len(row["scenes_today"]) >= 1


@pytest.mark.asyncio
async def test_student_cannot_access_ai_config(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/ai/config", headers=headers)
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_admin_ai_usage(client, seed_users):
    record_llm_usage(user_id=seed_users["student"].id, tokens=120, scene="chat_rag", model="qwen3.6-flash")
    record_llm_usage(user_id=seed_users["student"].id, tokens=80, scene="code_analysis", model="qwen3.6-flash")

    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/ai/usage", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["tokens_today"] >= 200
    assert body["data"]["calls_today"] >= 2
    assert len(body["data"]["daily_tokens_7d"]) == 7


def test_secret_crypto_roundtrip():
    plain = "sk-test-secret-key"
    cipher = encrypt_secret(plain)
    assert cipher != plain
    assert decrypt_secret(cipher) == plain
