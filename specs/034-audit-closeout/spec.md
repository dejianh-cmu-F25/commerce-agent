# Feature Specification: Production Audit Close-Out

**Feature Branch**: `034-audit-closeout`

**Created**: 2026-09-13

**Status**: Draft

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
- **Data quality**: n/a.
- **Edge & failure modes**: residual gaps are named, not hidden.
- **Scale envelope**: n/a.
- **Degradation**: n/a.
- **Change evidence**: the clause statuses reference the measured evidence.

## Success Criteria

- **SC-001**: Every clause has a current status + evidence + residual gap.
- **SC-002**: Every roadmap item is marked with its status.
- **SC-003**: The local gate passes.

## Assumptions

- The audit is a document, not code; the status reflects the merged evidence in
  `specs/RESULTS.md` and `evals/report.md`.
