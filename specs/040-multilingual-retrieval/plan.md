# Implementation Plan: Multilingual Retrieval Measurement

**Branch**: `040-multilingual-retrieval` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add a labeled multilingual query set, measure it keylessly in `evals/bench.py`
(report-only), render it in the report, and document the gap.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-1 | non-English coverage is measured, not assumed | PASS |
| P8 | keyless | PASS |
| EV-6 | the measurement is recorded | PASS |

## Project Structure

```text
evals/retrieval_set.py   # + MULTILINGUAL_SET (language label)
evals/bench.py           # measure it; store under "multilingual" (not gated)
evals/report.py          # render it as a labeled gap
scripts/check_results.py # validate the numbers
docs/clarify-vs-refuse.md; docs/edge-cases.md  # update the gap
```

## Design decisions

- **Separate set, separate result.** Adding non-English queries to the gated set
  would fail the English threshold for a reason the keyless retriever cannot fix.
  The multilingual set is measured and reported, clearly labeled as a gap.
- **Honest labeling.** The report says "gap (not gated)" so no one reads a low
  number as a regression.

## Complexity Tracking

> No violations; stdlib only.
