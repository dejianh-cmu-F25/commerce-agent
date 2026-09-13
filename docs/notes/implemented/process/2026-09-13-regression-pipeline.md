# Agent Note: Failures become named, root-caused regressions

Status: implemented (2026-09-13) — feature `033-regression-pipeline`

## Problem

RW-4/EV-5 require that a fix ship with a regression and that failures flow back
into the suite, but there was no mechanism: failures were fixed and the gold set
was edited ad hoc, with no record of *why* a guard existed or where it came from.
The trajectory-prefix regression set was minimal, and nothing enforced that a
fix kept its guard.

## Alternatives considered

- **Put the guard inline in the gold scenarios only.** No root cause, no source,
  no traceability — a reader cannot tell what failure a case prevents. Rejected.
- **Store arbitrary code per regression.** A promoted entry could inject code and
  a broken one could rot silently. Rejected.
- **A committed registry of named checks + a promotion script.** Chosen.

## Decision

- **`evals/regressions.json`**: each regression names `id`, `source`,
  `root_cause`, and `check`. The `check` resolves from a fixed map in
  `evals/regressions.py`, so an unknown name fails the gate.
- **`scripts/promote_regression.py`**: promotes a failure; it **refuses an empty
  root cause** (a regression without a cause is a symptom) and is idempotent by
  `id` (RD-2).
- **The gate runs every regression** (`evals/regressions.py`); coverage is
  rendered into the report.
- **Five cross-feature regressions** seeded: ungrounded id, return window,
  prompt injection (028), dirty price (027), dense outage (031).

## Consequences

- A fixed failure now has a durable, traceable guard: a reader sees the source and
  the root cause, and the gate keeps it green.
- The registry grows as incidents are root-caused — the pipeline, not the count,
  is the deliverable.
- **Residual gaps** (documented in `docs/regressions.md`): promotion is manual
  (no automatic export from the real eval), and the set is still small (5).
