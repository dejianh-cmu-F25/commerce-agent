# Feature Specification: Scale Boundaries (Large Corpus & Long Session)

**Feature Branch**: `037-scale-boundaries`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Extend the scale envelope to a large corpus (10k chunks) and a long
session (100 turns), measured and gated (SC-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A large corpus is measured (Priority: P1)

Retrieval over a synthetic 10,000-chunk corpus is measured at the target
concurrency; the p95 is reported and gated against a declared budget.

**Why this priority**: SC-1 names data volume; the corpus was tiny (9 chunks) and
the "large-corpus" residual was open.

**Independent Test**: Run the scale benchmark and read the large-corpus p95.

**Acceptance Scenarios**:

1. **Given** a 10k-chunk corpus, **When** retrieval runs at concurrency 16,
   **Then** p95 is measured and within budget.

---

### User Story 2 - A long session is measured (Priority: P1)

A single session of 100 scripted turns completes, and the log stays
reconstructable (SL-1) without unbounded blow-up.

**Independent Test**: Run 100 turns in one session; assert the turn count, the
event count, and that `derive_messages` succeeds.

**Acceptance Scenarios**:

1. **Given** 100 turns in one session, **When** the benchmark runs, **Then** the
   session has the expected events and the total time is within budget.

---

### Edge Cases

- **Synthetic corpus**: chunks are derived from the real corpus with a unique id,
  so the measurement is representative and deterministic.
- **Long session growth**: the event list grows linearly; the budget catches a
  super-linear regression (e.g., an O(n²) re-derivation).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scale benchmark MUST measure retrieval over a 10k-chunk corpus
  and a 100-turn session.
- **FR-002**: Both MUST have declared budgets and fail the gate on a breach.
- **FR-003**: Both MUST be rendered in the report and documented in
  `docs/scale.md`.

### Key Entities

- **Large-corpus boundary**: p95 retrieval latency over N chunks.
- **Long-session boundary**: wall-clock time and event count for L turns.

## Real-World Coverage

- **Input distribution**: a 10k-chunk corpus; a 100-turn session.
- **Data quality**: synthetic chunks carry unique ids (no duplicate collision).
- **Edge & failure modes**: a breach of either budget fails the gate; a session
  that is not reconstructable raises (SL-1).
- **Scale envelope**: this feature extends it (data volume + session length).
- **Degradation**: n/a (measurement).
- **Change evidence**: the measured large-corpus and long-session numbers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Large-corpus retrieval p95 at concurrency 16 ≤ 50,000 µs.
- **SC-002**: 100-turn session completes ≤ 5,000 ms with a reconstructable log.
- **SC-003**: Both are rendered and gated.
- **SC-004**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Data Provenance & Licensing

- n/a: the data/corpus is authored in-repo; there is no external data source.

## Assumptions

- The synthetic corpus is representative of size, not content; it measures the
  retrieval data-structure cost, not semantic quality.
