# Feature Specification: Production Audit Close-Out

**Feature Branch**: `034-audit-closeout`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Re-run the production audit after remediation: record the new status of
each clause and the residual gaps (RW/SC/EV).

## Context

`docs/production-audit.md` was the first application of the production clauses
(v1.3.0) and named nine remediation items (P0/P1/P2). Features 026–033 executed
them. The audit says "Re-run: after remediation" — this closes that loop.

## Requirements

- **FR-001**: The audit MUST record the **current** status of every clause with
  evidence and a residual gap, distinct from the as-found snapshot.
- **FR-002**: The roadmap MUST mark each item's status (done / partial).

## Real-World Coverage

- **Input distribution**: n/a (process/documentation).
- **Data quality**: n/a (a document, no data path).
- **Edge & failure modes**: residual gaps are named, not hidden.
- **Scale envelope**: n/a (a document; the system envelope is in `docs/scale.md`).
- **Degradation**: n/a (a document, no runtime path).
- **Change evidence**: the clause statuses reference the measured evidence.

## Success Criteria

- **SC-001**: Every clause has a current status + evidence + residual gap.
- **SC-002**: Every roadmap item is marked with its status.
- **SC-003**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- The audit is a document, not code; the status reflects the merged evidence in
  `specs/RESULTS.md` and `evals/report.md`.
