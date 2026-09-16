"""Guardrail aggregation and floors (feature 036, EV-3)."""

from __future__ import annotations

from pathlib import Path

from evals.guardrails import evaluate, load_history, record

_KEYLESS = {
    "segments": {"by_intent": {"search": {"passed": 1.0, "total": 1.0}}},
    "adversarial": {"safe_rate": 1.0},
    "regressions": {"coverage": 1.0},
    "data_quality": {"accuracy": 1.0},
    "fallbacks": {"coverage": 1.0},
    "scale": {
        "levels": [{"concurrency": 16, "turn": {"p95_us": 15.0}}],
        "slo": {"turn_p95_us": 10000.0},
        "envelope": {"target_concurrency": 16},
    },
}


def _by_name(guardrails) -> dict:
    return {g.name: g for g in guardrails}


def test_all_guardrails_within_floors() -> None:
    guardrails = evaluate(_KEYLESS)
    assert len(guardrails) >= 6
    assert all(g.ok for g in guardrails)


def test_a_regressed_quality_metric_fails() -> None:
    keyless = dict(_KEYLESS)
    keyless["adversarial"] = {"safe_rate": 0.5}
    guardrails = _by_name(evaluate(keyless))
    assert not guardrails["safety:adversarial_safe_rate"].ok


def test_record_appends_and_loads(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    result = {
        "metrics": [
            {"name": "quality:gold_pass_rate", "value": 1.0},
            {"name": "latency:turn_p95_us", "value": 0.5},
        ]
    }
    record(result, path)
    record(result, path)
    history = load_history(path)
    assert len(history) == 2
    assert history[-1]["metrics"]["latency:turn_p95_us"] == 0.5


def test_history_is_capped(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    result = {"metrics": [{"name": "x", "value": 1.0}]}
    for _ in range(5):
        record(result, path, limit=3)
    assert len(load_history(path)) == 3


def test_latency_is_at_most() -> None:
    keyless = dict(_KEYLESS)
    keyless["scale"] = {
        "levels": [{"concurrency": 16, "turn": {"p95_us": 20000.0}}],
        "slo": {"turn_p95_us": 10000.0},
        "envelope": {"target_concurrency": 16},
    }
    guardrails = _by_name(evaluate(keyless))
    assert not guardrails["latency:turn_p95_us"].ok
