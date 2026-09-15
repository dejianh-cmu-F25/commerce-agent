"""The results gate must notice a stale guardrail row, not only a missing one.

Regression: the guardrail check was one-directional (every declared metric must
appear in the report). When `cost:spent_cny` stopped being declared, its row stayed
in the rendered report for a commit and the gate passed — the report quoted a
metric nothing computed.
"""

from __future__ import annotations

from scripts.check_results import _check_report

ARTIFACTS = {
    "guardrails": {
        "metrics": [
            {
                "name": "quality:gold_pass_rate",
                "value": 1.0,
                "floor": 1.0,
                "direction": "at_least",
                "source": "segments",
            }
        ]
    }
}

REPORT = """## Guardrails

| Guardrail | Value | Δ prev | Floor | Direction | Source | Status |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `quality:gold_pass_rate` | 1.0 | +0.0000 | 1.0 | ≥ | `segments` | OK |
"""


def test_a_complete_report_passes_the_guardrail_check() -> None:
    failures = _check_report(ARTIFACTS, REPORT)
    assert not [f for f in failures if "guardrails" in f]


def test_an_undeclared_guardrail_row_fails() -> None:
    stale = REPORT + "| `cost:spent_cny` | 9.48 | +8.83 | 10.0 | ≤ | `budget` | OK |\n"
    failures = _check_report(ARTIFACTS, stale)
    assert any("undeclared row" in f and "cost:spent_cny" in f for f in failures)


def test_a_missing_declared_row_still_fails() -> None:
    failures = _check_report(ARTIFACTS, "## Guardrails\n\n| Guardrail |\n| --- |\n")
    assert any("expected row" in f for f in failures)
