# Feature Specification: Gates

**Feature Branch**: `020-gates`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Extract the inline write guardrails into an `app/gates/` pipeline
(provenance, return eligibility) with a shared context, so guardrails have one
home and can be composed and tested — preserving behavior exactly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guardrails in one place (Priority: P1)

Every write/render guardrail is a named gate that runs through one pipeline and
returns a decision with a reason.

**Why this priority**: The architecture reserves `app/gates/` as the write
guardrail pipeline (P3, PB-2), but the checks are currently inline in tools.

**Independent Test**: Run each gate directly and via the pipeline; assert the
decision and reason.

**Acceptance Scenarios**:

1. **Given** an id not issued in the session, **When** the provenance gate runs,
   **Then** it blocks with a reason naming the id.
2. **Given** an out-of-window order, **When** the return gate runs, **Then** it
   blocks with the policy reason.
3. **Given** a pipeline, **When** the first gate blocks, **Then** later gates do
   not run.

---

### User Story 2 - Behavior is unchanged (Priority: P1)

The tools use the gates but produce exactly the same outputs as before.

**Independent Test**: The existing tool and eval tests pass unchanged.

**Acceptance Scenarios**:

1. **Given** an ungrounded add, **When** the cart tool runs, **Then** it returns
   the same error JSON and status as before.
2. **Given** an eligible return, **When** `start_return` runs, **Then** it renders
   the same payload as before.

---

### Edge Cases

- **No order**: the return gate blocks with a reason.
- **Empty id list**: the provenance gate allows.
- **Multiple failures**: the pipeline returns the first block.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define `GateResult` (allowed + reason), a `Gate`
  contract (`name`, `check(context)`), and a `GateContext` carrying the session
  and the values gates need.
- **FR-002**: A `ProvenanceGate` MUST block when any id is not in the session's
  server-issued set (P4).
- **FR-003**: A `ReturnEligibilityGate` MUST wrap the return policy and block with
  its reason (P3, feature 014).
- **FR-004**: A `GatePipeline` MUST run gates in order and return the first block.
- **FR-005**: The cart and order tools MUST use the gates with byte-identical
  outputs to before (SC-002).
- **FR-006**: The gates MUST be pure/decision-only: they never mutate the session
  or the store (P3).

## Observability

- Gates are internal decisions; the enclosing tool call remains the traced span
  (OB-1). No new span is required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Gate unit tests cover allow/block and pipeline short-circuit.
- **SC-002**: All existing tests and evals pass with no assertion changes.
- **SC-003**: No tool output or status changes.
- **SC-004**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes.

## Assumptions

- This is a behavior-preserving refactor; no new guardrail is added.
- Merchant approval stays a web-endpoint concern (the model has no apply tool).
