# Feature Specification: Large-Catalog Boundary

**Feature Branch**: `041-large-catalog`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Measure storefront search over a large catalog (5k products), gated,
closing the RW-2/SC-1 data-volume residual.

> Complementary to `037-scale-boundaries`: 037 measures the **corpus** (knowledge
> chunks) and **session** boundaries; this spec measures the **catalog** boundary.
> Both extend the `029-scale-slo` framework; neither replaces the other.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A large catalog is measured (Priority: P1)

Catalog search over a synthetic 5,000-product SQLite storefront is measured at the
target concurrency; the p95 is reported and gated.

**Why this priority**: RW-2/SC-1 — the audit named "large-catalog scale untested";
the storefront's search is O(catalog) per query and must be measured.

**Independent Test**: Run the scale benchmark and read the large-catalog p95.

**Acceptance Scenarios**:

1. **Given** a 5k-product catalog, **When** search runs at concurrency 16,
   **Then** p95 is measured and within budget.

---

### Edge Cases

- **Synthetic products**: unique ids, varied titles/prices; deterministic.
- **The real path**: the SQLite storefront (row read + normalize + rank), not a
  shortcut.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scale benchmark MUST measure catalog search over a 5k-product
  SQLite storefront at the target concurrency.
- **FR-002**: It MUST have a declared budget and fail the gate on a breach.
- **FR-003**: It MUST be rendered in the report and documented in `docs/scale.md`.

### Key Entities

- **Large-catalog boundary**: p95 search latency over N products.

## Real-World Coverage

- **Input distribution**: a 5,000-product catalog.
- **Data quality**: synthetic products are valid; the storefront normalizes on
  read (feature 027).
- **Edge & failure modes**: a breach fails the gate; an invalid row is skipped.
- **Scale envelope**: this feature extends it (catalog volume).
- **Degradation**: n/a (measurement).
- **Change evidence**: the measured large-catalog p95.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Large-catalog search p95 at concurrency 16 is measured and ≤ budget.
- **SC-002**: The result is rendered and gated.
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

- The synthetic catalog measures the storefront's scan/rank cost, not relevance.
