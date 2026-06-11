from datetime import datetime, timedelta

from app.services.mastery import (
    compute_dashboard_kp_score,
    compute_kp_score,
    weight_for_source,
)


def test_compute_kp_score_empty():
    assert compute_kp_score([]) == 100


def test_compute_kp_score_single_recent():
    now = datetime(2026, 6, 10, 12, 0, 0)
    penalties = [(1.0, now - timedelta(days=1))]
    score = compute_kp_score(penalties, now=now)
    assert 75 <= score <= 85


def test_compute_kp_score_decay():
    now = datetime(2026, 6, 10, 12, 0, 0)
    recent = compute_kp_score([(1.0, now - timedelta(days=1))], now=now)
    old = compute_kp_score([(1.0, now - timedelta(days=60))], now=now)
    assert old > recent


def test_weight_for_source():
    assert weight_for_source("code_submission") == 1.0
    assert weight_for_source("chat_message") == 0.6


def test_compute_dashboard_kp_score_spreads_perfect_scores():
    scores = [
        compute_dashboard_kp_score(
            mastery_score=100,
            unmastered_wrong=0,
            total_wrong=0,
            sort_order=order,
            kp_id=kid,
        )
        for order, kid in [(1, 11), (2, 22), (3, 33), (4, 44), (5, 55)]
    ]
    assert len(set(scores)) >= 4
    assert all(52 <= s <= 92 for s in scores)


def test_compute_dashboard_kp_score_keeps_weak_low():
    score = compute_dashboard_kp_score(
        mastery_score=20,
        unmastered_wrong=3,
        total_wrong=3,
        sort_order=0,
        kp_id=1,
    )
    assert score <= 25
