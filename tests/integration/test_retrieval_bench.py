"""Integration tests for the retrieval benchmark (feature 022)."""

from __future__ import annotations

from evals.bench import CONFIGS, MIN_HIT_RATE, run_bench


def test_all_configs_meet_the_threshold():
    result = run_bench()
    assert set(result["configs"]) == set(CONFIGS)
    for config, metrics in result["configs"].items():
        assert metrics["hit_rate"] >= MIN_HIT_RATE, (config, metrics)


def test_metrics_are_deterministic():
    first = run_bench()
    second = run_bench()
    for config in CONFIGS:
        assert first["configs"][config]["hit_rate"] == second["configs"][config]["hit_rate"]
        assert first["configs"][config]["mrr"] == second["configs"][config]["mrr"]
