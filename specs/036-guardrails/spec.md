# Feature Specification: Guardrail Metrics

**Feature Branch**: `036-guardrails`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Declare the guardrail metrics (quality, safety, latency, cost) with
floors, aggregate them in the gate, render them, and require a guardrail statement
per measurable change (EV-3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A change cannot quietly trade away a guardrail (Priority: P1)

The keyless artifacts are aggregated into one guardrail table with declared
floors; the gate fails if any metric drops below its floor.

**Why this priority**: EV-3 — a change that improves its target metric must not
regress quality, safety, latency, or cost unnoticed.

**Independent Test**: Lower a guardrail metric and assert the gate fails.

**Acceptance Scenarios**:

1. **Given** the keyless artifacts, **When** the guardrail check runs, **Then**
   every metric is reported with its floor and pass/fail.
2. **Given** a metric below its floor, **When** the gate runs, **Then** it fails.

---

### User Story 2 - Every measurable change states its guardrail impact (Priority: P1)

A `measurable` change-log entry MUST state how the guardrails were affected.

**Independent Test**: Remove the `guardrails` field from a measurable entry and
assert the evidence gate fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST declare guardrail metrics with numeric floors
  (`docs/guardrails.md`).
- **FR-002**: A keyless aggregator MUST read the artifacts, compare each metric to
  its floor, and fail the gate on a regression.
- **FR-003**: The guardrails MUST be rendered in the report.
- **FR-004**: `scripts/check_change_evidence.py` MUST require a `guardrails`
  statement on every `measurable` entry.

### Key Entities

- **Guardrail**: `name`, `value`, `floor`, `direction` (`at_least` | `at_most`),
  `source`.

## Real-World Coverage

- **Input distribution**: the keyless artifact set (gold, adversarial, data,
  regressions, fallbacks, scale, cost).
- **Data quality**: the dirty-data accuracy is a guardrail.
- **Edge & failure modes**: a below-floor metric fails the gate; a missing source
  fails loud.
- **Scale envelope**: the latency guardrail is the turn p95 at the target
  concurrency (`docs/scale.md`).
- **Degradation**: the fallback coverage is a guardrail.
- **Change evidence**: this feature is the guardrail comparison (EV-3).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ≥ 6 guardrail metrics declared with floors and all satisfied.
- **SC-002**: A below-floor metric fails the gate.
- **SC-003**: A measurable entry without a guardrail statement fails the evidence
  gate.
- **SC-004**: The local gate passes.

## Assumptions

- Guardrails are read from the keyless artifacts, so the check is free and runs in
  the gate; the real (paid) eval's numbers are a snapshot and are not floors.
