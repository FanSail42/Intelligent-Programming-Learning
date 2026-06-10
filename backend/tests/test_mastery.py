from datetime import datetime, timedelta

from app.services.mastery import compute_kp_score, weight_for_source


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
