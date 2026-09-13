# Implementation Plan: Guardrail Trend History

**Branch**: `042-guardrail-history` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add a committed `evals/guardrail-history.jsonl`, a `--record` flag on
`evals/guardrails.py`, a delta in the result, a trend column in the report, and
documentation.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| EV-3 | a regression is visible over time | PASS |
| P8 | keyless | PASS |
| RD-2 | the history is append-only and capped | PASS |

## Project Structure

```text
evals/guardrails.py          # + load_history/record/--record/trend
evals/guardrail-history.jsonl  # NEW (seeded with one entry)
evals/report.py              # + delta column
docs/guardrails.md           # the recording policy
tests/unit/test_guardrails.py
```

## Design decisions

- **Explicit recording.** The gate must not dirty the working tree, so appending
  is `--record` only; the gate validates the current values against the floors.
- **Cap, don't grow forever.** Keep the last N entries so the committed file stays
  small.
- **Delta, not a chart.** A per-metric delta vs the previous entry is enough to
  see a drift without a rendering dependency.

## Complexity Tracking

> No violations; stdlib only.
