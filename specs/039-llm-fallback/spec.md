# Feature Specification: LLM Provider Fallback

**Feature Branch**: `039-llm-fallback`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Give the LLM a config-gated fallback provider that serves when the
primary fails before emitting, recorded as a degradation (RD-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A provider outage falls back before emitting (Priority: P1)

When the configured LLM provider fails **before** emitting any event, the turn is
served by a configured fallback provider and the degradation is recorded.

**Why this priority**: RD-1 — the audit's residual "the LLM has no provider
fallback"; a provider outage should not fail the turn when a fallback is
configured.

**Independent Test**: Wrap a failing primary with a mock secondary; assert the
stream is served by the secondary and one degradation is recorded.

**Acceptance Scenarios**:

1. **Given** a primary that fails before emitting, **When** a turn streams,
   **Then** the fallback's events are emitted and the degradation is recorded.
2. **Given** a primary that fails **after** emitting a delta, **When** the turn
   streams, **Then** the error propagates (deltas cannot be un-sent).

---

### User Story 2 - The fallback is config-gated (Priority: P1)

With no fallback provider configured, behavior is the primary alone.

**Independent Test**: Build the LLM with no fallback configured; assert it is the
primary (no wrapper).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A `FallbackLLM` MUST serve the secondary when the primary fails
  before emitting, record a `Degradation`, and NOT retry a failed primary.
- **FR-002**: A mid-stream primary failure MUST propagate (no partial fallback).
- **FR-003**: `llm.fallback_provider` MUST gate the behavior (empty = no
  fallback).
- **FR-004**: The keyless fallback benchmark MUST exercise the LLM fallback and
  the gate MUST pass.

### Key Entities

- **FallbackLLM**: a primary + secondary client with a `degraded` flag and
  `degradations`.

## Real-World Coverage

- **Input distribution**: a provider outage before and after the first token.
- **Data quality**: n/a (the fallback passes messages through; no data path).
- **Edge & failure modes**: pre-emit failure → fallback; mid-stream failure →
  propagate; disabled → primary only.
- **Scale envelope**: O(1) per stream; see `docs/scale.md`.
- **Degradation**: this feature extends the LLM degradation row.
- **Change evidence**: the fallback coverage (change log).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Fallback coverage **6/6** on the labeled dependency set.
- **SC-002**: A mid-stream failure propagates.
- **SC-003**: No fallback configured → primary only.
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

- The fallback provider is a separate configuration (provider/model/key); it is
  off by default because a second provider is a real cost/credential choice.
