import pytest

from tests.conftest import login


@pytest.mark.asyncio
async def test_login_success(client, seed_users):
    data = await login(client, "student", "Student123!")
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, seed_users):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "wrong-password"},
    )
    body = resp.json()
    assert body["code"] == 40101


@pytest.mark.asyncio
async def test_refresh_token(client, seed_users):
    tokens = await login(client, "teacher", "Teacher123!")
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["access_token"]


@pytest.mark.asyncio
async def test_logout_blacklist(client, seed_users):
    tokens = await login(client, "admin", "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert resp.json()["code"] == 0

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["code"] == 40101


@pytest.mark.asyncio
async def test_me(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "student"
    assert body["data"]["role"] == "student"
