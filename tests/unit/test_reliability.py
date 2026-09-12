"""Unit tests for reliability metrics (feature 023)."""

from __future__ import annotations

from app.evaluation.reliability import aggregate


def test_pass_at_1_and_pass_pow_k():
    tasks = [[True, True, True], [True, False, False]]
    result = aggregate(tasks, k=3)
    assert result.runs == 6
    assert result.successes == 4
    assert result.pass_at_1 == round(4 / 6, 4)
    assert result.pass_at_k == 1.0  # every task has at least one success
    assert result.pass_pow_k == 0.5  # only the first task succeeds all 3


def test_all_failures_and_empty():
    result = aggregate([[False, False]], k=2)
    assert result.pass_at_1 == 0.0
    assert result.pass_at_k == 0.0
    assert result.pass_pow_k == 0.0

    empty = aggregate([], k=3)
    assert empty.runs == 0
    assert empty.pass_at_1 == 0.0
