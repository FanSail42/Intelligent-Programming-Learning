"""Integration tests: material upload response time and representative purge."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dashboard_demo_data import TRACK_COURSES, seed_dashboard_demo  # noqa: E402
from generate_dashboard_materials import generate_all  # noqa: E402
from purge_representative_materials import purge_materials  # noqa: E402
from tests.conftest import login  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def dashboard_demo_pdfs():
    generate_all()
    yield


@pytest.fixture
def seeded_dashboard(db_session, seed_users):
    return seed_dashboard_demo(db_session)


@pytest.mark.asyncio
async def test_upload_returns_before_background_dispatch(
    client, seed_users, seed_course, seed_warehouses
):
    """Upload HTTP should return quickly; processing is deferred."""
    teacher = seed_users["teacher"]
    tokens = await login(client, teacher.username, "Teacher123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    content = b"# fast upload\n" * 5

    dispatch_calls: list[int] = []

    def capture_dispatch(material_id: int) -> None:
        dispatch_calls.append(material_id)

    with patch(
        "app.api.v1.materials.dispatch_material_processing",
        side_effect=capture_dispatch,
    ):
        started = time.perf_counter()
        resp = await client.post(
            "/api/v1/materials/upload",
            headers=headers,
            data={"course_id": str(seed_course.id)},
            files={"file": ("fast.md", content, "text/markdown")},
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)

    body = resp.json()
    assert body["code"] == 0, body
    assert elapsed_ms < 3000, f"upload HTTP too slow: {elapsed_ms}ms"
    assert len(dispatch_calls) == 1
    assert dispatch_calls[0] == body["data"]["material_id"]


@pytest.mark.asyncio
async def test_purge_keeps_only_representative_materials(db_session, seeded_dashboard):
    report = purge_materials(dry_run=False, reprocess=False)

    from app.models.material import CourseMaterial

    kept = (
        db_session.query(CourseMaterial)
        .filter(CourseMaterial.deleted == 0)
        .order_by(CourseMaterial.id.asc())
        .all()
    )
    track_ids = set(report["track_courses"].values())
    assert kept, "expected representative materials to remain"
    assert all(m.course_id in track_ids for m in kept)
    assert report["removed_materials"] >= 0
    assert report["kept_materials"] == len(kept)

    for spec in TRACK_COURSES:
        course_id = report["track_courses"].get(spec["name"])
        if not course_id:
            continue
        names = {m.original_name for m in kept if m.course_id == course_id}
        assert names, f"no materials kept for {spec['name']}"


@pytest.mark.asyncio
async def test_chroma_vectors_match_kept_materials(db_session, seeded_dashboard):
    from app.models.material import CourseMaterial, MaterialStatus
    from app.services.vector_store import get_vector_store

    purge_materials(dry_run=False, reprocess=False)

    ready_ids = {
        m.id
        for m in db_session.query(CourseMaterial)
        .filter(CourseMaterial.deleted == 0, CourseMaterial.status == MaterialStatus.ready)
        .all()
    }
    store = get_vector_store()
    all_rows = store._collection.get(include=["metadatas"])
    metas = all_rows.get("metadatas") or []
    orphan = [
        meta.get("material_id")
        for meta in metas
        if meta and int(meta.get("material_id", -1)) not in ready_ids
    ]
    assert not orphan, f"orphan chroma vectors for material_ids: {orphan[:10]}"
