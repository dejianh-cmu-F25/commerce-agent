# Implementation Plan: Edge & Failure Enumeration

**Branch**: `035-edge-cases` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `docs/edge-cases.md` (the cross-cutting matrix), strengthen the
`## Real-World Coverage` check in `scripts/spec_review.py`, add a corpus test,
and refresh the stale scale notes.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-3 | boundaries enumerated with a behavior each | PASS |
| P1 | the spec is the source of truth; the review enforces it | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
docs/edge-cases.md               # NEW: the boundary matrix
scripts/spec_review.py           # + six-bullet coverage check
tests/unit/test_spec_coverage.py # NEW: corpus invariant
specs/0*/spec.md                 # refresh stale scale notes
```

## Design decisions

- **One canonical doc.** The cross-cutting boundaries live in one place; a spec
  references it and adds only feature-specific edges.
- **Enforce in the review, not by convention.** A missing/empty bullet fails the
  gate, so the enumeration cannot silently rot.
- **Refresh, don't rewrite.** Stale "(gap)" notes become pointers to the measured
  envelope; genuine gaps stay.

## Complexity Tracking

> No violations.
