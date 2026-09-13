# Implementation Plan: Large-Catalog Boundary

**Branch**: `041-large-catalog` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Extend `evals/scale.py` with a 5k-product SQLite storefront search measurement,
budget, report line, and doc.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-2 / SC-1 | catalog data volume measured at the boundary | PASS |
| SC-3 | a budget is declared and gated | PASS |
| P8 | keyless | PASS |

## Project Structure

```text
evals/scale.py            # + large-catalog search measurement + budget
docs/scale.md             # document the dimension
tests/unit/test_scale.py  # + SLO case
```

## Design decisions

- **Measure the real path.** The SQLite storefront (read rows + normalize + rank)
  is measured, not an in-memory shortcut.
- **Honest budget.** The search is O(catalog) per query; the budget is set to
  catch a super-linear regression, not to claim production capacity.

## Complexity Tracking

> No violations; stdlib only.
