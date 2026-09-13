# Implementation Plan: Data Quality

**Branch**: `027-data-quality` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `app/data/quality.py` (pure normalizers), apply them in the SQLite storefront
(repair/strict via `data.quality`), add a repair script, and a keyless
data-quality benchmark rendered in the report. No new dependency.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-2 | validate/normalize at boundaries; defined behavior + repair path | PASS |
| PB-1 | `data.quality` selects repair/strict; strict fails loud | PASS |
| RD-2 | repair is idempotent and reports what it changed | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
app/data/quality.py             # NEW: normalizers
app/adapters/storefront_sqlite.py   # apply normalizers at read
app/core/settings.py            # + DataSettings(quality)
evals/data_quality_set.py       # NEW: labeled dirty inputs
evals/data_quality.py           # NEW: benchmark + gate
scripts/repair_storefront.py    # NEW: repair path
evals/report.py                 # render the data-quality section
tests/unit/test_data_quality.py
tests/integration/test_storefront_dirty.py
config/settings.yaml; .env.example
docs/notes/implemented/production/...-data-quality.md
```

## Design decisions

- **Pure normalizers, applied at the boundary.** The storefront is the data
  boundary; it normalizes on read so the domain never sees dirty data.
- **Reject, don't clamp.** A negative price is invalid, not zero; an
  unparseable value is skipped with a count, or raises in `strict`.
- **Repair is a script, not a hidden migration.** It rewrites/removes rows and
  reports the counts (traceable, RD-2).
- **Measured.** A labeled set scores the normalizers; the gate enforces 1.0.

## Complexity Tracking

> No violations; stdlib only.
