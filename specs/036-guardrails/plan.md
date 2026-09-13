# Implementation Plan: Guardrail Metrics

**Branch**: `036-guardrails` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `evals/guardrails.py` (aggregate the keyless artifacts into guardrail metrics
with floors, fail the gate on regression), render them, require a guardrail
statement per measurable change, and document the policy.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| EV-3 | guardrails compared, not regressed | PASS |
| EV-1 | measurable changes state a guardrail impact | PASS |
| P8 | keyless aggregation | PASS |

## Project Structure

```text
evals/guardrails.py              # NEW: aggregate + floor check
docs/guardrails.md               # NEW: metrics + floors + policy
evals/report.py; scripts/check_results.py; scripts/ci.sh
scripts/check_change_evidence.py # require guardrails on measurable entries
specs/change-log.json            # backfill the guardrails field
tests/unit/test_guardrails.py
```

## Design decisions

- **Aggregate, don't recompute.** The metrics are already produced by the other
  keyless evals; the guardrail check reads the artifact, so it is free and cannot
  disagree with the report.
- **Floors, not targets.** A floor is the minimum acceptable; a metric above it is
  fine. Direction is explicit (`at_least` / `at_most`).
- **Required per change.** EV-3 is only real if a measurable change must state its
  guardrail impact; the evidence gate enforces it.

## Complexity Tracking

> No violations; stdlib only.
