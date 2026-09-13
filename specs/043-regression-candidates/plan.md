# Implementation Plan: Regression Candidates

**Branch**: `043-regression-candidates` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Record per-failure detail in the real eval, add
`scripts/export_regression_candidates.py` (deduped, idempotent), a test, and the
documented flow.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| EV-5 | failures become regressions (export is automatic) | PASS |
| RW-4 | the root cause stays human before promotion | PASS |
| RD-2 | the export is idempotent | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
evals/agent_eval.py                      # + per-failure records
scripts/export_regression_candidates.py  # NEW: results -> candidates (deduped)
docs/regressions.md                      # document the flow
tests/unit/test_regression_candidates.py
```

## Design decisions

- **Export, don't promote.** The export captures evidence automatically; a human
  still writes the root cause and promotes (RW-4). A candidate is not a
  regression and is not gated.
- **Dedupe by (task, category).** Many seeds of the same failure are one
  candidate.
- **No-op without results.** The results file is uncommitted; a missing file is
  normal and must not fail.

## Complexity Tracking

> No violations; stdlib only.
