import pytest

from tests.conftest import login


@pytest.mark.asyncio
async def test_admin_list_students(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "student"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    usernames = {item["username"] for item in body["data"]["list"]}
    assert "student" in usernames
    assert "teacher" not in usernames
    assert all(item["role"] == "student" for item in body["data"]["list"])


@pytest.mark.asyncio
async def test_admin_list_requires_role(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/users", headers=headers)
    assert resp.json()["code"] == 40001


@pytest.mark.asyncio
async def test_admin_create_student_and_login(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "new_student",
            "password": "Student123!",
            "role": "student",
        },
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["role"] == "student"

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "new_student", "password": "Student123!"},
    )
    assert login_resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_admin_create_teacher(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "new_teacher",
            "password": "Teacher123!",
            "role": "teacher",
        },
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["role"] == "teacher"


@pytest.mark.asyncio
async def test_admin_duplicate_username(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "student",
            "password": "Student123!",
            "role": "student",
        },
    )
    assert resp.json()["code"] == 40001


@pytest.mark.asyncio
async def test_admin_disable_user_blocks_login(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "temp_student",
            "password": "Student123!",
            "role": "student",
        },
    )
    user_id = create_resp.json()["data"]["id"]

    update_resp = await client.put(
        f"/api/v1/admin/users/{user_id}",
        headers=headers,
        params={"role": "student"},
        json={"status": "disabled"},
    )
    assert update_resp.json()["code"] == 0

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "temp_student", "password": "Student123!"},
    )
    assert login_resp.json()["code"] == 40101


@pytest.mark.asyncio
async def test_admin_reset_password(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "pwd_student",
            "password": "Student123!",
            "role": "student",
        },
    )
    user_id = create_resp.json()["data"]["id"]

    await client.put(
        f"/api/v1/admin/users/{user_id}",
        headers=headers,
        params={"role": "student"},
        json={"password": "NewPass123!"},
    )

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "pwd_student", "password": "Student123!"},
    )
    assert old_login.json()["code"] == 40101

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "pwd_student", "password": "NewPass123!"},
    )
    assert new_login.json()["code"] == 0


@pytest.mark.asyncio
async def test_admin_delete_user(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    create_resp = await client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "username": "del_student",
            "password": "Student123!",
            "role": "student",
        },
    )
    user_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(
        f"/api/v1/admin/users/{user_id}",
        headers=headers,
        params={"role": "student"},
    )
    assert del_resp.json()["code"] == 0

    list_resp = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "student", "username": "del_student"},
    )
    assert list_resp.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_admin_cannot_delete_self(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.delete(
        f"/api/v1/admin/users/{seed_users['admin'].id}",
        headers=headers,
        params={"role": "student"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_admin_role_mismatch_on_update(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.put(
        f"/api/v1/admin/users/{seed_users['student'].id}",
        headers=headers,
        params={"role": "teacher"},
        json={"status": "disabled"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_teacher_forbidden(client, seed_users):
    tokens = await login(client, seed_users["teacher"].username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "student"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_student_forbidden(client, seed_users):
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "student"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_admin_filter_teachers(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        params={"role": "teacher"},
    )
    data = resp.json()["data"]
    assert data["total"] >= 1
    assert all(item["role"] == "teacher" for item in data["list"])


@pytest.mark.asyncio
async def test_admin_overview(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/api/v1/admin/overview", headers=headers)
    assert resp.json()["code"] == 0
    data = resp.json()["data"]
    assert data["students"]["total"] >= 1
    assert data["teachers"]["total"] >= 1
    assert "courses" in data
    assert isinstance(data["recent_logs"], list)


@pytest.mark.asyncio
async def test_admin_logs(client, seed_users):
    tokens = await login(client, seed_users["admin"].username, "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    await client.post(
        "/api/v1/auth/login",
        json={"username": seed_users["admin"].username, "password": "Admin123!"},
    )

    resp = await client.get(
        "/api/v1/admin/logs",
        headers=headers,
        params={"action": "login"},
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["total"] >= 1
