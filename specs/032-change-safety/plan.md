# Implementation Plan: Change Safety

**Branch**: `032-change-safety` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `blast_radius` and `rollback` to every change-log entry (backfilled), require
them in the gate, render them in the report, document the seam map, and extend the
PR template.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SC-4 | blast radius + rollback stated per change | PASS |
| EV-6 | the change log is the auditable record; fields added to it | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
specs/change-log.json            # + blast_radius, rollback per entry
scripts/check_results.py         # require both on every entry
scripts/check_change_evidence.py # require both on the current entry
evals/report.py                  # render both columns
docs/change-safety.md            # seam map + rollback policy
.github/pull_request_template.md # Blast radius & rollback section
tests/unit/test_change_log.py    # fields present on every entry
```

## Design decisions

- **Per change, in the log.** SC-4 is a property of a change, not a spec; the
  change log is already the per-change record, so the fields live there.
- **Backfill, don't grandfather.** Every existing entry gets an honest value
  (derived from its area/evidence), so the invariant holds for the whole corpus.
- **Gate on presence, review on quality.** The gate ensures the fields exist; the
  PR template ensures a human writes them meaningfully.

## Complexity Tracking

> No violations; stdlib only.
