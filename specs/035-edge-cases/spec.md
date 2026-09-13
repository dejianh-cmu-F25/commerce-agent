# Feature Specification: Edge & Failure Enumeration

**Feature Branch**: `035-edge-cases`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Enumerate the cross-cutting edge/failure boundaries with a defined
behavior each; strengthen the spec coverage check; refresh the stale per-spec
gaps (RW-3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The boundaries are enumerated once (Priority: P1)

A single canonical document lists the cross-cutting edge and failure boundaries —
empty input, oversized input, unknown ids, malformed tool JSON, missing
dependency, budget exhaustion, concurrency, partial failure — each with a defined
behavior and where it is enforced.

**Why this priority**: RW-3 — "not enumerated comprehensively; many boundaries
undefined". A reviewer should not have to reconstruct the boundary list per spec.

**Independent Test**: Read `docs/edge-cases.md`; every row names a behavior and a
guard/test.

**Acceptance Scenarios**:

1. **Given** the doc, **When** read, **Then** every boundary has a defined
   behavior and a pointer to where it is enforced.

---

### User Story 2 - A spec must enumerate its coverage (Priority: P1)

The self-review fails a spec whose `## Real-World Coverage` omits any of the six
bullets or leaves one empty.

**Independent Test**: Remove a bullet and assert the review fails.

**Acceptance Scenarios**:

1. **Given** a spec missing the `Edge & failure modes` bullet, **When** the
   review runs, **Then** it fails.

---

### User Story 3 - Stale gaps are refreshed (Priority: P2)

Per-spec "Scale envelope: not measured (gap)" notes are updated to point at the
now-measured system envelope (`docs/scale.md`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A canonical `docs/edge-cases.md` MUST enumerate the cross-cutting
  boundaries with a defined behavior and an enforcement pointer each.
- **FR-002**: `scripts/spec_review.py` MUST fail a spec whose `## Real-World
  Coverage` omits a bullet or leaves it empty (RW-3).
- **FR-003**: A corpus test MUST enforce the six bullets on every spec.
- **FR-004**: Stale "not measured (gap)" scale notes MUST reference
  `docs/scale.md`.

## Real-World Coverage

- **Input distribution**: empty, oversized, adversarial, and malformed inputs
  (cross-referenced to `evals/adversarial.py`).
- **Data quality**: dirty data is defined in `docs/edge-cases.md` and enforced by
  `app/data/quality.py`.
- **Edge & failure modes**: this feature **is** the enumeration; each boundary has
  a behavior and an enforcement pointer.
- **Scale envelope**: the system envelope is measured in `docs/scale.md`; this
  feature is O(1) documentation.
- **Degradation**: a missing dependency degrades via `docs/degradation.md`.
- **Change evidence**: the review + corpus test enforce the enumeration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every spec has all six coverage bullets with content (corpus test).
- **SC-002**: The review fails a spec with a missing/short bullet.
- **SC-003**: `docs/edge-cases.md` covers ≥ 10 boundaries.
- **SC-004**: The local gate passes.

## Assumptions

- The canonical doc is the cross-cutting list; a spec adds only feature-specific
  boundaries.
