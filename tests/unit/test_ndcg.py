"""Graded retrieval metrics (feature 046, discovery)."""

from __future__ import annotations

from app.evaluation.retrieval_metrics import evaluate_graded, ndcg_at_k


def test_ndcg_perfect_ranking_is_one() -> None:
    assert ndcg_at_k([1.0, 0.1, 0.0], [1.0, 0.1, 0.0], 3) == 1.0


def test_ndcg_penalises_inversion() -> None:
    # the relevant item is ranked last -> below a perfect ranking
    assert ndcg_at_k([0.0, 0.0, 1.0], [1.0, 0.0, 0.0], 3) < 1.0


def test_ndcg_zero_when_no_relevant() -> None:
    assert ndcg_at_k([0.0, 0.0], [0.0, 0.0], 2) == 0.0


def test_evaluate_graded_averages() -> None:
    metrics = evaluate_graded([([1.0, 0.0], [1.0, 0.0]), ([0.0], [1.0])], k=2)
    assert metrics.cases == 2
    assert 0.0 <= metrics.ndcg <= 1.0
    assert metrics.hit_rate == 0.5
