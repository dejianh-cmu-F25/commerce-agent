# Implementation Plan: Eval Report View

**Branch**: `025-eval-report-view` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `GET /report` (reads `evals/report.md`) and a Report tab that renders the
markdown through the existing sanitizing `MessageResponse`. No new dependency.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| WV-1 | Web Acceptance + Observability in the spec | PASS |
| WV-6 | empty/loading/success/error/disabled defined | PASS |
| WV-8 | fluid column; tables scroll in-container | PASS |
| WV-9 | markdown rendered through the sanitizing renderer | PASS |
| P8 | no key; reads a committed file | PASS |

## Project Structure

```text
web/main.py                          # GET /report
frontend/src/lib/report.ts           # fetch client
frontend/src/components/app/report-view.tsx
frontend/src/App.tsx                 # Report tab
tests/integration/test_report_api.py
docs/architecture.md; Agent Note
```

## Design decisions

- **Static artifact, not regeneration.** The view reads `evals/report.md`; the
  gate regenerates the keyless sections, real runs the real ones.
- **Reuse the sanitizing renderer.** `MessageResponse` (Streamdown) renders GFM
  tables and sanitizes; no new renderer.
- **Empty, not error, when absent.** A missing report is a normal state.

## Complexity Tracking

> No violations; no new dependency.
