# Feature Specification: Failure-to-Regression Pipeline

**Feature Branch**: `033-regression-pipeline`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Turn failures into named regressions with a root cause: a registry, a
promotion script, a keyless runner in the gate, and a documented workflow
(RW-4, EV-5).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A failure becomes a named regression (Priority: P1)

When a real failure is root-caused, it is promoted into a registry entry that
names the failure, its source, its root cause, and a keyless check. The check
runs in the gate, so the failure cannot silently return.

**Why this priority**: RW-4/EV-5 — a fix is not done until it ships with a
regression, and production failures must flow back into the suite.

**Independent Test**: Promote a failure and assert the registry gains an entry
and the runner exercises it.

**Acceptance Scenarios**:

1. **Given** a failure with a root cause, **When** it is promoted, **Then** the
   registry has a new entry with `id`, `source`, `root_cause`, and `check`.
2. **Given** a registered regression, **When** the gate runs, **Then** its check
   is exercised and a failure fails the gate.

---

### User Story 2 - The regressions are traceable (Priority: P2)

Each registry entry names where the failure came from and why it happened, so a
reader can connect the guard to the incident.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A regression MUST be a named entry with `id`, `source`,
  `root_cause`, and `check` (a known keyless check).
- **FR-002**: The gate MUST run every registered regression and fail on any
  failure.
- **FR-003**: A promotion script MUST append an entry from a failure, requiring a
  root cause (no regression without a cause).
- **FR-004**: The workflow MUST be documented (`docs/regressions.md`).

### Key Entities

- **Regression**: `id`, `source`, `root_cause`, `check` — a durable guard for one
  past failure.

## Real-World Coverage

- **Input distribution**: cross-feature failures — an ungrounded id, an
  out-of-window return, an injection, a dirty price, a dense outage.
- **Data quality**: the dirty-price regression guards normalization.
- **Edge & failure modes**: an unknown check name fails the gate (fail loud).
- **Scale envelope**: the set is O(cases); see `docs/scale.md`.
- **Degradation**: n/a (reporting only; see `docs/edge-cases.md`).
- **Change evidence**: the regression set and its coverage (change log).

## Observability

- The report shows the regression set and coverage; the gate enforces it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The registry has ≥ 5 named regressions, each with a root cause.
- **SC-002**: The gate runs them and fails on any failure.
- **SC-003**: Promoting a failure without a root cause is rejected.
- **SC-004**: The local gate passes.

## Assumptions

- The registry is a committed JSON file; a check is a named keyless callable, not
  free-form code (so a regression cannot rot silently).
- Some checks reuse the gold scenarios; the regression adds the *named, traced*
  guard, not a new mechanism.
