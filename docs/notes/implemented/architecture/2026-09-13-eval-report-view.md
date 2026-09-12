# Agent Note: The eval report is a committed artifact, rendered in the browser

Status: implemented (2026-09-13) — feature `025-eval-report-view`

## Problem

The evaluation numbers live in `evals/report.md`, but a reviewer had to open the
repository to see them. The web app already surfaces Chat, Traces, Merchant,
Memory, Scenarios, and Metrics; the evidence for the harness was the one thing
missing from the browser.

## Alternatives considered

- **Regenerate the report on request.** Fresh, but it would run the benchmark (and
  optionally spend budget) inside a web request, and could clobber the committed
  real-model numbers. Rejected.
- **Return structured JSON and hand-build tables.** More control over layout, but
  duplicates the report's formatting and drifts from the markdown. Rejected.
- **Render the markdown with a new renderer.** Unnecessary; the sanitizing
  Streamdown renderer already handles GFM tables (WV-9).

## Decision

- **The report is a static, committed artifact.** `GET /report` reads
  `evals/report.md`; the gate regenerates the keyless sections and `--real` runs
  the real ones, so the file is the single source of truth.
- **The Report view renders it through `MessageResponse`.** Streamdown renders
  headings and tables and sanitizes; a missing file is an empty state, not an
  error.
- **Read-only.** The view never regenerates or writes.

## Consequences

- The numbers that justify the project are visible in the browser alongside the
  demo, with the model, seeds, and command recorded in the report itself.
- The view shows whatever is committed; a stale report stays stale until someone
  runs `evals/report.py --write` (or a real run). This is intentional: the report
  is a deliberate snapshot, not a live computation.
- No new dependency and no new span; the report remains the observability
  artifact.
