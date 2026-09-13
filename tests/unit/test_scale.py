"""Scale-envelope SLO evaluation (feature 029, SC-3)."""

from __future__ import annotations

from evals.scale import SLO, evaluate_slo


def _result(level: dict) -> dict:
    return {"envelope": {"target_concurrency": 16}, "levels": [level]}


def _level(retrieval_p95: float, turn_p95: float, error_rate: float = 0.0) -> dict:
    return {
        "concurrency": 16,
        "retrieval": {"p95_us": retrieval_p95},
        "turn": {"p95_us": turn_p95, "error_rate": error_rate},
    }


def test_slo_passes_within_budget() -> None:
    assert evaluate_slo(_result(_level(5.0, 10.0))) == []


def test_slo_fails_on_latency_breach() -> None:
    assert evaluate_slo(_result(_level(SLO["retrieval_p95_us"] + 1, 10.0)))
    assert evaluate_slo(_result(_level(5.0, SLO["turn_p95_us"] + 1)))


def test_slo_fails_on_error_rate() -> None:
    assert evaluate_slo(_result(_level(5.0, 10.0, error_rate=0.5)))


def test_slo_fails_without_a_target_measurement() -> None:
    assert evaluate_slo({"envelope": {"target_concurrency": 16}, "levels": []})
