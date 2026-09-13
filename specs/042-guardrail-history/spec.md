# Feature Specification: Guardrail Trend History

**Feature Branch**: `042-guardrail-history`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Record guardrail values over time in a committed history and render the
trend, closing the EV-3 residual (no trend history).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A guardrail regression is visible over time (Priority: P1)

Guardrail values are appended to a committed history when recorded; the report
shows the current value and the delta from the previous recorded run.

**Why this priority**: EV-3 says regressions must be visible. A floor catches a
drop below the minimum; a trend shows a drift before it hits the floor.

**Independent Test**: Record twice and assert the history grows and the report
shows a delta.

**Acceptance Scenarios**:

1. **Given** a recorded history, **When** the report renders, **Then** each
   guardrail shows its value and its delta vs the previous entry.

---

### Edge Cases

- **First run**: no previous entry → the delta is "—".
- **The gate must not write**: recording is explicit (`--record`), so a normal
  gate run does not dirty the working tree.
- **Non-deterministic metrics**: latency/cost vary; the delta reflects that.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A committed history file MUST store one entry per recorded run
  (`date`, `metrics`).
- **FR-002**: `evals/guardrails.py --record` MUST append the current values; the
  gate MUST run without recording.
- **FR-003**: The report MUST show the delta vs the previous entry.
- **FR-004**: The history MUST be capped (no unbounded growth).

### Key Entities

- **History entry**: `date`, `metrics` (name → value).

## Real-World Coverage

- **Input distribution**: the keyless artifact set over successive runs.
- **Data quality**: n/a (the history stores aggregate metric values only).
- **Edge & failure modes**: a missing history renders "—"; the cap drops the
  oldest entry.
- **Scale envelope**: the file is capped; see `docs/guardrails.md`.
- **Degradation**: n/a (a reporting feature; no runtime path).
- **Change evidence**: the trend (report + history).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The history file exists and is well-formed; recording appends.
- **SC-002**: The report shows a delta column.
- **SC-003**: A normal gate run does not modify the history.
- **SC-004**: The local gate passes.

## Assumptions

- Recording is a manual step after a meaningful run (like the real-eval snapshot);
  the gate validates, it does not record.
