# Implementation Plan: Agent Evaluation Upgrade

**Branch**: `023-agent-evaluation` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add pure evaluation modules (`agent_metrics`, `failure`, `reliability`,
`rubric`), a keyless **ablation** runner, an opt-in **real** runner (DeepSeek,
budget-capped), and report sections. The gate runs the keyless ablation; real
runs are manual and produce the committed `evals/report.md` sections.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P7 evals first-class | richer, reproducible evaluation | PASS |
| P4 grounding | the judge veto encodes "no fabrication"; metrics count ungrounded attempts | PASS |
| P8 keyless default | ablation + gate are keyless; real runs opt-in | PASS |
| HR-12 budgets | real runs capped; cost per run/task reported | PASS |
| RD-1 resilience | bad judge JSON falls back to deterministic checks | PASS |
| TT-2 deterministic | keyless metrics are deterministic | PASS |
| HR-11 | new cases/metrics are data; documented | PASS |

## Project Structure

```text
app/evaluation/agent_metrics.py  # process metrics from events
app/evaluation/failure.py        # first-error attribution
app/evaluation/reliability.py    # Pass@1/Pass@k/Best@k/Pass^k
app/evaluation/rubric.py         # Rubric + judge (DeepSeek) + fallback
app/core/settings.py             # EvaluationSettings: seeds, pass_k, judge, real, cap
evals/ablation.py                # keyless feature ablation
evals/agent_eval.py              # opt-in real runner
evals/real_cases.py              # outcome-based real cases
evals/report.py                  # + ablation / real sections
tests/unit/test_agent_metrics.py, test_failure.py, test_reliability.py, test_rubric.py
tests/integration/test_ablation.py
scripts/ci.sh                    # run the ablation (keyless)
docs/architecture.md; Agent Note
```

## Design decisions

- **Pure modules, thin runners.** Metrics/attribution/reliability/rubric are pure
  functions (unit-tested); the runners wire them to real events.
- **Outcome-based real predicates.** Real runs assert final state (components,
  cart, grounded answer), never prose or exact tool sequences (TT-2).
- **Veto = grounding.** The judge's veto mirrors P4 (no fabricated
  price/stock/policy); a bad judge response falls back to rule checks.
- **Budget-capped real runs.** `evaluation.max_cost_cny` plus the global budget;
  the runner stops and reports partial results.
- **Report merge.** Keyless sections update in the gate; real sections update only
  on `--real`, so a keyless run never clobbers real numbers.

## Complexity Tracking

> Adds evaluation code and one opt-in real path; no new dependency (DeepSeek via
> the existing client).
