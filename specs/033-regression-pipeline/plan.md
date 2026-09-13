# Implementation Plan: Failure-to-Regression Pipeline

**Branch**: `033-regression-pipeline` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add a committed regression registry (`evals/regressions.json`), a typed loader
(`app/evaluation/regressions.py`), a keyless runner in the gate
(`evals/regressions.py`), a promotion script
(`scripts/promote_regression.py`), and the workflow doc.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-4 | a fix ships with a regression; the set grows | PASS |
| EV-5 | failures become regressions (a pipeline) | PASS |
| RD-2 | promotion is idempotent by `id` | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
app/evaluation/regressions.py    # NEW: Regression + load
evals/regressions.json           # NEW: the registry (committed)
evals/regressions.py             # NEW: keyless runner + gate
scripts/promote_regression.py    # NEW: promote a failure (requires root cause)
evals/report.py; scripts/check_results.py; scripts/ci.sh
docs/regressions.md
tests/unit/test_regressions.py
```

## Design decisions

- **Named checks, not embedded code.** A regression references a check by name
  from a fixed map, so a promoted entry cannot inject arbitrary code and a broken
  reference fails loud.
- **Root cause is required.** Promotion refuses an entry without a root cause —
  the point of RW-4 is that the cause is understood, not that the symptom is
  recorded.
- **Idempotent by id.** Re-promoting the same id updates in place (RD-2).

## Complexity Tracking

> No violations; stdlib only.
