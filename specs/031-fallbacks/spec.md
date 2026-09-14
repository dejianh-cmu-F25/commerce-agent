# Feature Specification: Declared Fallbacks

**Feature Branch**: `031-fallbacks`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Give each external dependency a deterministic, config-gated fallback
that degrades observably; wrap the retriever (dense → keyless lexical) and score
the coverage keylessly (RD-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A dependency failure degrades, not crashes (Priority: P1)

When the configured retriever fails (a vector store or embedding outage), the
knowledge tool falls back to the keyless lexical retriever instead of raising,
and the degradation is recorded.

**Why this priority**: RD-1 — every external dependency has a deterministic
fallback; the system degrades observably rather than failing silently.

**Independent Test**: Wrap a failing retriever with a lexical fallback, retrieve,
and assert results are served, `degraded` is true, and the degradation is
recorded once.

**Acceptance Scenarios**:

1. **Given** a failing primary retriever, **When** a query runs, **Then** the
   fallback serves results and one degradation is recorded.
2. **Given** a healthy primary, **When** a query runs, **Then** no degradation is
   recorded.
3. **Given** the primary has failed once, **When** more queries run, **Then** the
   primary is not retried (fast, deterministic fallback).

---

### User Story 2 - Degradation is observable and config-gated (Priority: P1)

The fallback can be disabled by config; a degradation is visible (recorded on the
wrapper and, when present, traced).

**Independent Test**: Disable the fallback and assert the primary's failure
propagates.

**Acceptance Scenarios**:

1. **Given** `resilience.fallback_enabled=false`, **When** the retriever fails,
   **Then** the failure propagates (no hidden fallback).

---

### User Story 3 - Coverage is measured (Priority: P2)

A keyless benchmark scores how many dependencies have a declared, exercised
fallback; the gate enforces it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a generic fallback wrapper that serves the
  secondary on a primary failure, records a `Degradation`, and does not retry a
  failed primary.
- **FR-002**: The knowledge retriever MUST fall back dense → keyless lexical when
  `resilience.fallback_enabled` (default on).
- **FR-003**: The degradation MUST be observable (recorded; traced when a tracer
  is present).
- **FR-004**: A keyless benchmark MUST score the fallback coverage and run in the
  gate.

### Key Entities

- **Degradation**: `component`, `primary`, `fallback`, `reason` — one record per
  failed dependency.

## Real-World Coverage

- **Input distribution**: a failing vector store / embedding outage; a missing
  knowledge directory; an LLM provider failure.
- **Data quality**: n/a (the fallback composes retrievers; see `docs/edge-cases.md`).
- **Edge & failure modes**: the fallback triggers once and is not retried; a
  disabled fallback propagates the error.
- **Scale envelope**: the wrapper is O(1) per call; see `docs/scale.md`.
- **Degradation**: this feature **is** the degradation rule (RD-1).
- **Change evidence**: the fallback coverage (change log).

## Observability

- The wrapper exposes `degraded` and `degradations`; the report shows the
  coverage; a failure is attributed (SC-2).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Fallback coverage **4/4** on the labeled dependency set.
- **SC-002**: A degraded retriever serves results and records one degradation.
- **SC-003**: Disabling the fallback propagates the failure.
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

- The lexical retriever is a legitimate degraded mode (it is the keyless
  default); the fallback trades recall for availability.
- The LLM has no provider fallback; its failure degrades to a surfaced error
  (RD-1 "observably"), not a second provider.
