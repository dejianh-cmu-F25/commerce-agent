# Implementation Plan: Scale Boundaries

**Branch**: `037-scale-boundaries` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Extend `evals/scale.py` with two measured boundaries — a 10k-chunk retrieval and
a 100-turn session — with budgets, rendered in the report and documented.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SC-1 | data volume + session length measured at the boundary | PASS |
| SC-3 | budgets declared and gated | PASS |
| SL-1 | the long session asserts the log stays reconstructable | PASS |
| P8 | keyless | PASS |

## Project Structure

```text
evals/scale.py        # + large-corpus + long-session measurements and budgets
docs/scale.md         # document the new dimensions
tests/unit/test_scale.py  # + evaluate_slo cases for the new budgets
```

## Design decisions

- **Synthetic, representative corpus.** Derive 10k chunks from the real ones with
  unique ids; deterministic and free.
- **Measure the data structure, not the content.** The large-corpus number is
  about retrieval cost at volume, not semantic quality (the benchmark owns that).
- **The long session asserts SL-1.** Time alone is not enough; the log must still
  be reconstructable after 100 turns.

## Complexity Tracking

> No violations; stdlib only.
