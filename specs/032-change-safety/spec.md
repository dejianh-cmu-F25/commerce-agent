# Feature Specification: Change Safety (Blast Radius & Rollback)

**Feature Branch**: `032-change-safety`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: State the blast radius and rollback for every change: add the fields to
the change log, gate them, document the seam map, and add a PR template (SC-4).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every change states its blast radius and rollback (Priority: P1)

Each change-log entry carries a `blast_radius` (what the change can affect) and a
`rollback` (how to undo it). The gate fails an entry that omits either.

**Why this priority**: SC-4 — changes must be localized behind seams and the
blast radius / rollback must be stated; a team must be able to undo a change
without a big-bang rewrite.

**Independent Test**: Remove `blast_radius` from an entry and assert the gate
fails.

**Acceptance Scenarios**:

1. **Given** a change-log entry without `blast_radius` or `rollback`, **When**
   the gate runs, **Then** it fails.
2. **Given** every entry has both fields, **When** the gate runs, **Then** it
   passes and the report renders them.

---

### Edge Cases

- **Initial commit**: blast radius is the whole repo; rollback is `git revert`.
- **A seam-level change**: blast radius names the module/port it is behind.
- **A data change**: rollback states whether a migration is reversible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every change-log entry MUST have non-empty `blast_radius` and
  `rollback` fields.
- **FR-002**: The gate MUST fail when either field is missing (SC-4).
- **FR-003**: The report MUST render both fields for each change.
- **FR-004**: The seam map and rollback policy MUST be documented
  (`docs/change-safety.md`).
- **FR-005**: The PR template MUST ask for the blast radius and rollback.

### Key Entities

- **Blast radius**: what a change can affect (module, seam, data, surface).
- **Rollback**: how to undo it (revert, config toggle, migration).

## Real-World Coverage

- **Input distribution**: n/a (process/documentation).
- **Data quality**: rollback states migration reversibility.
- **Edge & failure modes**: a missing field fails the gate.
- **Scale envelope**: n/a (process/docs; the system envelope is in `docs/scale.md`).
- **Degradation**: rollback is the degradation path for a bad change.
- **Change evidence**: the blast radius/rollback fields (change log).

## Observability

- The change log and the rendered report show both fields per change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of change-log entries have `blast_radius` and `rollback`.
- **SC-002**: Removing either fails the gate.
- **SC-003**: The report renders both; `docs/change-safety.md` exists.
- **SC-004**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- The deployable unit is the app image; rollback is a revert + rebuild, with no
  destructive SQLite migration in the current design.
