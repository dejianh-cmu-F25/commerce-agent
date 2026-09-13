# Feature Specification: Segmented Metrics

**Feature Branch**: `030-segmented-metrics`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Segment the keyless metrics by intent and by tool so a failure can be
localized; render the segments in the report and validate them in the gate (SC-2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Localize a failure by segment (Priority: P1)

Aggregate pass rates hide which slice is failing. Each gold scenario carries an
**intent**, and each tool call carries a status, so the report shows pass rate by
intent and error rate by tool.

**Why this priority**: SC-2 — a team must be able to localize a problem under
load; an aggregate "11/12" cannot.

**Independent Test**: Run the gold scenarios and read the by-intent and by-tool
tables; a failing scenario is attributable to its intent and its tools.

**Acceptance Scenarios**:

1. **Given** the gold set, **When** the segments are computed, **Then** every
   scenario's intent appears with its pass rate and every called tool appears
   with its error rate.

---

### Edge Cases

- **A tool called by several intents**: its segment aggregates all calls.
- **A tool that errors by design** (`ungrounded_add_rejected`): the error is
  counted and attributed, not hidden.
- **A scenario with no tools**: contributes to its intent, not to any tool.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each gold scenario MUST declare an `intent`.
- **FR-002**: The runner MUST record each tool call's name and status.
- **FR-003**: The system MUST compute pass rate by intent and error rate by tool
  (pure functions).
- **FR-004**: The gate MUST render the segments and validate them against the
  artifact.

### Key Entities

- **Intent**: the customer job a scenario exercises (`search`, `cart`, `orders`,
  `returns`, …).
- **Tool segment**: calls and errors for one tool name.

## Real-World Coverage

- **Input distribution**: the 12 gold scenarios across 9 intents and 12 tools.
- **Data quality**: n/a (segmentation reads run results, not raw data).
- **Edge & failure modes**: a by-design tool error is attributed to its tool.
- **Scale envelope**: segments are O(scenarios + tool calls); see `docs/scale.md`.
- **Degradation**: n/a (reporting only).
- **Change evidence**: the segmented pass/error rates (report + change log).

## Observability

- `evals/report.md` gains a `## Segmented metrics` section (by intent, by tool);
  the gate validates it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every scenario intent appears with a pass rate; every called tool
  appears with an error rate.
- **SC-002**: The segments match the artifact (gate-validated).
- **SC-003**: The local gate passes.

## Assumptions

- Single-tenant, single-model keyless run; tenant and model segmentation are
  documented gaps (see `docs/diagnosability.md`).
