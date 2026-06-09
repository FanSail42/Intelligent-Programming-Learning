import pytest

from app.core.deps import require_roles
from app.core.exceptions import BusinessException
from app.models.user import UserRole
from tests.conftest import login


@pytest.mark.asyncio
async def test_require_roles_allows_teacher(client, seed_users):
    tokens = await login(client, "teacher", "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/courses", headers=headers)
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_require_roles_blocks_student(client, seed_users):
    tokens = await login(client, "student", "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await client.get("/api/v1/courses", headers=headers)
    assert resp.json()["code"] == 40301


def test_require_roles_dependency():
    checker = require_roles(UserRole.admin)

    class FakeUser:
        role = UserRole.student

    import asyncio

    async def run():
        try:
            await checker(FakeUser())  # type: ignore[arg-type]
            return False
        except BusinessException as exc:
            return exc.code == 40301

    assert asyncio.run(run()) is True
