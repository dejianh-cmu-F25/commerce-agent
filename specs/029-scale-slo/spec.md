# Feature Specification: Scale Envelope & SLOs

**Feature Branch**: `029-scale-slo`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Declare the scale dimensions and SLO budgets (latency, error rate,
cost), measure the keyless envelope at increasing concurrency, render it, and
fail the gate on regression (SC-1, SC-3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The envelope is declared and measured (Priority: P1)

The system states the scale dimensions it must survive (catalog size, knowledge
chunks, concurrency, session length, cost) and the **measured** behavior at the
boundary, not just "it works small".

**Independent Test**: Run the keyless scale benchmark and read the latency
percentiles and throughput at each concurrency level.

**Acceptance Scenarios**:

1. **Given** the keyless stack, **When** the benchmark runs at concurrency
   1/4/16/64, **Then** it reports p50/p95 latency and throughput per level.

---

### User Story 2 - SLOs are declared and enforced (Priority: P1)

Latency, error, and cost budgets are declared; a regression below budget fails
the gate.

**Independent Test**: Evaluate the measured result against the declared budgets.

**Acceptance Scenarios**:

1. **Given** the target concurrency, **When** a measured p95 exceeds its budget,
   **Then** the gate fails.
2. **Given** the target concurrency, **When** the error rate exceeds 0, **Then**
   the gate fails.

---

### Edge Cases

- **Very fast ops**: a p50 of ~0 ms is valid; the budget is on p95.
- **Timing noise on a loaded CI host**: budgets are generous regression guards,
  not tight targets; the report carries the raw numbers.
- **Cost**: the budget cap (HR-12) is the cost SLO; it is already tracked.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST declare its scale dimensions and SLO budgets in a
  canonical doc (`docs/scale.md`).
- **FR-002**: A keyless benchmark MUST measure latency percentiles, throughput,
  and error rate at increasing concurrency and write them to the report.
- **FR-003**: The gate MUST fail when a declared SLO is breached at the target
  concurrency (SC-3: regressions visible).
- **FR-004**: The measured numbers MUST be rendered in `evals/report.md` and
  validated by `scripts/check_results.py`.

### Key Entities

- **SLO**: a named budget (latency p95, error rate, cost) with a threshold.
- **Envelope**: the tested dimensions (sizes, concurrency, ops) and the measured
  behavior at the boundary.

## Real-World Coverage

- **Input distribution**: the keyless stack under 1–64 concurrent operations
  (retrieval and a full scripted agent turn).
- **Data quality**: n/a (no external data; the measurement is synthetic).
- **Edge & failure modes**: error rate is measured, not assumed; a breach fails
  the gate.
- **Scale envelope**: this feature **is** the envelope — catalog size, knowledge
  chunks, concurrency, ops per level, and the measured p50/p95/throughput.
- **Degradation**: the envelope's boundary is the point where latency grows
  super-linearly or errors appear; beyond it is an explicit, documented gap.
- **Change evidence**: the measured SLOs (change log).

## Observability

- The report shows the per-level latency/throughput table; the gate enforces the
  declared budgets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The benchmark runs at 1/4/16/64 concurrency and reports p50/p95 and
  throughput per level.
- **SC-002**: At the target concurrency, retrieval p95 ≤ 2000 µs, turn p95 ≤
  10000 µs, error rate 0 (the declared budgets in `docs/scale.md`; these guard
  harness overhead, not provider latency).
- **SC-003**: A breached budget fails the gate.
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

- Latency is measured on the keyless stack (no network); it bounds harness
  overhead, not provider latency (the real eval measures that).
- Budgets are regression guards sized for a developer laptop/CI, not production
  capacity targets.
