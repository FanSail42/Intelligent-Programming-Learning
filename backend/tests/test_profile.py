import pytest

from tests.conftest import login


@pytest.mark.asyncio
async def test_profile_summary_student(client, seed_users):
    student = seed_users["student"]
    headers = {"Authorization": f"Bearer {(await login(client, student.username, 'Student123!'))['access_token']}"}
    resp = await client.get("/api/v1/auth/profile/summary", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "student"
    assert body["data"]["role"] == "student"
    assert "login_count" in body["data"]
    assert body["data"]["ai_usage"] is not None


@pytest.mark.asyncio
async def test_profile_summary_teacher(client, seed_users):
    teacher = seed_users["teacher"]
    headers = {"Authorization": f"Bearer {(await login(client, teacher.username, 'Teacher123!'))['access_token']}"}
    resp = await client.get("/api/v1/auth/profile/summary", headers=headers)
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["role"] == "teacher"
    assert body["data"]["ai_usage"] is None


@pytest.mark.asyncio
async def test_profile_update_username(client, seed_users):
    student = seed_users["student"]
    headers = {"Authorization": f"Bearer {(await login(client, student.username, 'Student123!'))['access_token']}"}
    resp = await client.patch(
        "/api/v1/auth/profile/username",
        headers=headers,
        json={"new_username": "student_renamed", "current_password": "Student123!"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["username"] == "student_renamed"

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["data"]["username"] == "student_renamed"

    # restore
    await client.patch(
        "/api/v1/auth/profile/username",
        headers=headers,
        json={"new_username": "student", "current_password": "Student123!"},
    )


@pytest.mark.asyncio
async def test_profile_update_username_wrong_password(client, seed_users):
    student = seed_users["student"]
    headers = {"Authorization": f"Bearer {(await login(client, student.username, 'Student123!'))['access_token']}"}
    resp = await client.patch(
        "/api/v1/auth/profile/username",
        headers=headers,
        json={"new_username": "other_name", "current_password": "wrong-pass"},
    )
    assert resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_profile_change_password(client, seed_users):
    student = seed_users["student"]
    headers = {"Authorization": f"Bearer {(await login(client, student.username, 'Student123!'))['access_token']}"}
    resp = await client.patch(
        "/api/v1/auth/profile/password",
        headers=headers,
        json={"current_password": "Student123!", "new_password": "NewPass123!"},
    )
    assert resp.json()["code"] == 0

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "Student123!"},
    )
    assert old_login.json()["code"] == 40101

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "student", "password": "NewPass123!"},
    )
    assert new_login.json()["code"] == 0

    # restore
    restore_headers = {
        "Authorization": f"Bearer {new_login.json()['data']['access_token']}"
    }
    await client.patch(
        "/api/v1/auth/profile/password",
        headers=restore_headers,
        json={"current_password": "NewPass123!", "new_password": "Student123!"},
    )
