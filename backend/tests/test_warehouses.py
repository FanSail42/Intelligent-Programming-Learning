from unittest.mock import patch

import pytest

from app.models.material import CourseMaterial, MaterialStatus, MaterialType
from app.models.warehouse import MaterialWarehouse, WarehouseKind
from tests.conftest import login


@pytest.mark.asyncio
async def test_list_warehouses(client, seed_users, seed_warehouses):
    tokens = await login(client, "teacher", "Teacher123!")
    resp = await client.get(
        "/api/v1/warehouses",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 6


@pytest.mark.asyncio
async def test_admin_create_warehouse(client, seed_users, seed_warehouses):
    tokens = await login(client, "admin", "Admin123!")
    resp = await client.post(
        "/api/v1/warehouses",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={
            "name": "备用PDF库",
            "material_type": "pdf",
            "icon": "📚",
            "color": "#9b59b6",
            "sort_order": 10,
        },
    )
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["name"] == "备用PDF库"


@pytest.mark.asyncio
async def test_teacher_cannot_create_warehouse(client, seed_users, seed_warehouses):
    tokens = await login(client, "teacher", "Teacher123!")
    resp = await client.post(
        "/api/v1/warehouses",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"name": "非法", "material_type": "pdf"},
    )
    assert resp.json()["code"] == 40301


@pytest.mark.asyncio
async def test_warehouse_materials_pagination_and_search(
    client, db_session, seed_users, seed_course, seed_warehouses
):
    pdf_wh = next(w for w in seed_warehouses if w.material_type == MaterialType.pdf)
    teacher = seed_users["teacher"]

    for i, uname in enumerate(["teacher", "admin"]):
        material = CourseMaterial(
            course_id=seed_course.id,
            warehouse_id=pdf_wh.id,
            uploaded_by=seed_users[uname].id,
            type=MaterialType.pdf,
            file_path=f"/tmp/f{i}.pdf",
            original_name=f"doc{i}.pdf",
            status=MaterialStatus.ready,
        )
        db_session.add(material)
    db_session.commit()

    tokens = await login(client, teacher.username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        f"/api/v1/warehouses/{pdf_wh.id}/materials",
        headers=headers,
        params={"page_num": 1, "page_size": 1, "teacher_name": "teach"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert body["data"]["page_size"] == 1
    assert len(body["data"]["list"]) == 1
    assert body["data"]["list"][0]["uploader_name"] == "teacher"


@pytest.mark.asyncio
async def test_warehouse_material_name_search(
    client, db_session, seed_users, seed_course, seed_warehouses
):
    pdf_wh = next(w for w in seed_warehouses if w.material_type == MaterialType.pdf)
    material = CourseMaterial(
        course_id=seed_course.id,
        warehouse_id=pdf_wh.id,
        uploaded_by=seed_users["teacher"].id,
        type=MaterialType.pdf,
        file_path="/tmp/intro.pdf",
        original_name="Python入门讲义.pdf",
        status=MaterialStatus.ready,
    )
    db_session.add(material)
    db_session.commit()

    tokens = await login(client, "teacher", "Teacher123!")
    resp = await client.get(
        f"/api/v1/warehouses/{pdf_wh.id}/materials",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        params={"material_name": "入门"},
    )
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 1
    assert "入门" in body["data"]["list"][0]["original_name"]


@pytest.mark.asyncio
async def test_admin_assign_to_course_warehouse(
    client, db_session, seed_users, seed_course, seed_warehouses
):
    pdf_wh = next(
        w for w in seed_warehouses
        if w.warehouse_kind.value == "file_type" and w.material_type == MaterialType.pdf
    )
    python_wh = next(
        w for w in seed_warehouses
        if w.warehouse_kind.value == "course" and w.course_subject.value == "python"
    )
    material = CourseMaterial(
        course_id=seed_course.id,
        warehouse_id=pdf_wh.id,
        uploaded_by=seed_users["teacher"].id,
        type=MaterialType.pdf,
        file_path="/tmp/py.pdf",
        original_name="py.pdf",
        status=MaterialStatus.ready,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    tokens = await login(client, "admin", "Admin123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.post(
        f"/api/v1/warehouses/{python_wh.id}/assign",
        headers=headers,
        json={"material_ids": [material.id]},
    )
    assert resp.json()["code"] == 0

    db_session.refresh(material)
    assert material.warehouse_id == python_wh.id

    resp2 = await client.post(
        f"/api/v1/warehouses/{python_wh.id}/unassign",
        headers=headers,
        json={"material_ids": [material.id]},
    )
    assert resp2.json()["code"] == 0
    db_session.refresh(material)
    assert material.warehouse_id == pdf_wh.id


@pytest.mark.asyncio
async def test_admin_delete_empty_warehouse(client, db_session, seed_users, seed_warehouses):
    wh = MaterialWarehouse(
        name="临时库",
        warehouse_kind=WarehouseKind.file_type,
        material_type=MaterialType.txt,
        icon="📦",
        color="#000",
    )
    db_session.add(wh)
    db_session.commit()
    db_session.refresh(wh)

    tokens = await login(client, "admin", "Admin123!")
    resp = await client.delete(
        f"/api/v1/warehouses/{wh.id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.json()["code"] == 0


@pytest.mark.asyncio
async def test_upload_assigns_warehouse(client, seed_users, seed_course, seed_warehouses):
    teacher = seed_users["teacher"]
    tokens = await login(client, teacher.username, "Teacher123!")
    content = b"# test\n" * 10

    with patch("app.api.v1.materials._dispatch_process"):
        resp = await client.post(
            "/api/v1/materials/upload",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            data={"course_id": str(seed_course.id)},
            files={"file": ("note.md", content, "text/markdown")},
        )
    assert resp.json()["code"] == 0
