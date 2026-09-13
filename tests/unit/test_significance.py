"""Unit tests for paired significance (feature 026)."""

from __future__ import annotations

from app.evaluation.significance import bootstrap_ci, mcnemar_p, paired_delta


def test_mcnemar_known_values():
    # 2 discordant pairs, both in favour of the candidate: p = 0.5
    baseline = [False, False, True, True]
    candidate = [True, True, True, True]
    assert mcnemar_p(baseline, candidate) == 0.5
    # No discordant pairs -> p = 1.0
    assert mcnemar_p([True, False], [True, False]) == 1.0


def test_bootstrap_ci_is_deterministic_and_ordered():
    values = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    low, high = bootstrap_ci(values)
    assert (low, high) == bootstrap_ci(values)
    assert low <= high
    assert bootstrap_ci([]) == (0.0, 0.0)


def test_paired_delta_reports_effect_and_sample():
    baseline = [False, False, True, True]
    candidate = [True, True, True, True]
    result = paired_delta(baseline, candidate)
    assert result.delta == 0.5
    assert result.n == 4
    assert result.p_value == 0.5
    assert result.ci_low <= result.delta <= result.ci_high
