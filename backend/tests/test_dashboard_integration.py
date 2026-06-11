"""Integration tests for learning dashboard across three representative courses."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dashboard_demo_data import TRACK_COURSES, seed_dashboard_demo  # noqa: E402
from generate_dashboard_materials import generate_all  # noqa: E402
from tests.conftest import login  # noqa: E402

COURSE_KEYS = [spec["key"] for spec in TRACK_COURSES]


@pytest.fixture(scope="session", autouse=True)
def dashboard_demo_pdfs():
    generate_all()
    yield


@pytest.fixture
def seeded_dashboard(db_session, seed_users):
    report = seed_dashboard_demo(db_session)
    assert report["totals"]["wrong_all"] >= 20
    return report


def _course_id_by_key(report: dict, key: str) -> int:
    for item in report["courses"]:
        if item["key"] == key:
            return item["id"]
    raise KeyError(key)


@pytest.mark.asyncio
@pytest.mark.parametrize("course_key", COURSE_KEYS)
async def test_wrong_book_stats_sources_and_categories(
    client, seeded_dashboard, seed_users, course_key
):
    course_id = _course_id_by_key(seeded_dashboard, course_key)
    tokens = await login(client, seed_users["student"].username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get(
        "/api/v1/learning/wrong-book/stats",
        headers=headers,
        params={"course_id": course_id, "days": 7},
    )
    assert resp.status_code == 200
    stats = resp.json()["data"]

    assert stats["summary"]["total"] >= 5
    assert len(stats["by_source"]) == 2
    source_map = {item["source_type"]: item["count"] for item in stats["by_source"]}
    assert source_map["code_submission"] > 0
    assert source_map["chat_message"] > 0

    categories = {item["category"] for item in stats["by_category"]}
    assert "semantic_error" in categories or "syntax_error" in categories
    assert "chat_no_context" in categories
    assert len(stats["by_category"]) >= 2
    assert len(stats["trend"]) == 7
    pie_total = sum(item.get("value", item.get("count", 0)) for item in stats["mastered_pie"])
    assert pie_total >= stats["summary"]["total"]


@pytest.mark.asyncio
@pytest.mark.parametrize("course_key", COURSE_KEYS)
async def test_dashboard_weak_kps_and_recommendations(
    client, db_session, seeded_dashboard, seed_users, course_key
):
    from app.models.course import CourseStudent

    course_id = _course_id_by_key(seeded_dashboard, course_key)
    student = seed_users["student"]
    enrolled = (
        db_session.query(CourseStudent)
        .filter(CourseStudent.course_id == course_id, CourseStudent.user_id == student.id)
        .first()
    )
    assert enrolled is not None

    tokens = await login(client, student.username, "Student123!")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    dash = await client.get(
        "/api/v1/learning/dashboard",
        headers=headers,
        params={"course_id": course_id},
    )
    assert dash.status_code == 200
    data = dash.json()["data"]
    assert data["summary"]["total_events_7d"] >= 0
    assert len(data["weak_kps"]) >= 1

    rec = await client.get(
        "/api/v1/learning/recommendations",
        headers=headers,
        params={"course_id": course_id},
    )
    assert rec.status_code == 200
    items = rec.json()["data"]
    assert len(items) >= 1
    assert items[0]["kp_name"]
    assert items[0]["action_type"] in {
        "review_wrong_book",
        "review_material",
        "practice_code",
    }


@pytest.mark.asyncio
async def test_dashboard_demo_totals(seeded_dashboard):
    totals = seeded_dashboard["totals"]
    assert totals["wrong_all"] >= 20
    assert totals["wrong_all"] <= 50
    assert totals["materials"] >= 18
    assert len(seeded_dashboard["courses"]) == 3
