"""Guardrail aggregation and floors (feature 036, EV-3)."""

from __future__ import annotations

from evals.guardrails import evaluate

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
    guardrails = evaluate(_KEYLESS, {"spent_cny": 0.66})
    assert len(guardrails) >= 6
    assert all(g.ok for g in guardrails)


def test_a_regressed_quality_metric_fails() -> None:
    keyless = dict(_KEYLESS)
    keyless["adversarial"] = {"safe_rate": 0.5}
    guardrails = _by_name(evaluate(keyless, {"spent_cny": 0.66}))
    assert not guardrails["safety:adversarial_safe_rate"].ok


def test_latency_and_cost_are_at_most() -> None:
    keyless = dict(_KEYLESS)
    keyless["scale"] = {
        "levels": [{"concurrency": 16, "turn": {"p95_us": 20000.0}}],
        "slo": {"turn_p95_us": 10000.0},
        "envelope": {"target_concurrency": 16},
    }
    guardrails = _by_name(evaluate(keyless, {"spent_cny": 11.0}))
    assert not guardrails["latency:turn_p95_us"].ok
    assert not guardrails["cost:spent_cny"].ok
