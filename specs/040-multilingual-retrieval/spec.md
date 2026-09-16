# Feature Specification: Multilingual Retrieval Measurement

**Feature Branch**: `040-multilingual-retrieval`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Measure non-English retrieval over the English corpus as an honest,
reported gap (RW-1).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The non-English gap is measured, not assumed (Priority: P1)

Non-English policy queries are run against the keyless retriever over the English
corpus; the hit-rate is reported by language and labeled as a gap. It is **not**
gated (the keyless lexical retriever cannot cross languages), so the measurement
is honest rather than a hidden failure.

**Why this priority**: RW-1 — the audit named non-English coverage as unmeasured;
"we know it is weak" is not a measurement.

**Independent Test**: Run the benchmark and read the multilingual hit-rate.

**Acceptance Scenarios**:

1. **Given** Spanish/French/German/Chinese policy queries, **When** the keyless
   retriever runs, **Then** the hit-rate is measured per language and reported.

---

### Edge Cases

- **The gate must not fail on a known gap**: the multilingual numbers are
  reported and documented, not added to the gated English hit-rate.
- **A query that happens to share a token** (e.g., "warranty" loanword) may hit;
  the per-language number reflects that honestly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A multilingual query set MUST exist with a language label and an
  expected source.
- **FR-002**: The keyless benchmark MUST measure it and store the result.
- **FR-003**: The result MUST be rendered in the report and validated, and
  documented as a gap (not gated).
- **FR-004**: The gated English hit-rate MUST be unchanged.

### Key Entities

- **Multilingual case**: `query`, `expected_source`, `language`.

## Real-World Coverage

- **Input distribution**: non-English policy queries (es/fr/de/zh) over an
  English corpus.
- **Data quality**: n/a (the metric isolates language mismatch; no data path).
- **Edge & failure modes**: a known gap is measured and labeled, not hidden; the
  English gate is unaffected.
- **Scale envelope**: the set is O(cases); see `docs/scale.md`.
- **Degradation**: n/a (a measurement feature; no runtime path).
- **Change evidence**: the measured multilingual hit-rate (change log).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The multilingual hit-rate is measured and rendered per language.
- **SC-002**: The gated English hit-rate is unchanged.
- **SC-003**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Data Provenance & Licensing

- n/a: the data/corpus is authored in-repo; there is no external data source.

## Assumptions

- Closing the gap needs multilingual embeddings, a larger change; this feature
  measures and documents it.
