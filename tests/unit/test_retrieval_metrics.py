"""Unit tests for the retrieval metrics (feature 022)."""

from __future__ import annotations

from app.evaluation.retrieval_metrics import (
    evaluate_retrieval,
    hit_at_k,
    recall_at_k,
    reciprocal_rank,
)


def test_hit_recall_and_reciprocal_rank():
    assert hit_at_k(["a", "b"], {"a"}, 2) == 1.0
    assert hit_at_k(["a", "b"], {"c"}, 2) == 0.0
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, 3) == 1.0
    assert recall_at_k(["a", "b", "c"], {"a", "z"}, 3) == 0.5
    assert reciprocal_rank(["x", "a"], {"a"}) == 0.5
    assert reciprocal_rank(["x", "y"], {"a"}) == 0.0


def test_evaluate_averages_and_handles_empty():
    metrics = evaluate_retrieval([(["a"], {"a"}), (["x"], {"b"})], 1)
    assert metrics.cases == 2
    assert metrics.hit_rate == 0.5
    assert metrics.recall == 0.5
    assert metrics.mrr == 0.5

    empty = evaluate_retrieval([], 3)
    assert empty.cases == 0
    assert empty.hit_rate == 0.0
