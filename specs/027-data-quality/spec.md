# Feature Specification: Data Quality

**Feature Branch**: `027-data-quality`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Validate and normalize data at the storefront boundaries; define
behavior for missing, dirty, or conflicting rows; provide a repair path; and
measure the normalization with a keyless benchmark (RW-2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dirty rows have defined behavior (Priority: P1)

The storefront validates and normalizes catalog and order rows before they enter
the domain. A row that cannot be salvaged is skipped with a reason; a fixable
value (a price with a currency symbol, a stock that says "out of stock", padding)
is normalized.

**Why this priority**: RW-2 — no silent assumptions about upstream data; dirty
data must not crash the agent or leak garbage into a grounded answer.

**Independent Test**: Insert dirty rows and assert the storefront returns only
normalized, valid records and never raises in `repair` mode.

**Acceptance Scenarios**:

1. **Given** a price `"$1,299.00"` and stock `"out of stock"`, **When** a product
   row is normalized, **Then** the price is `1299.00` and the stock is `0`.
2. **Given** a row with no title or an unparseable price, **When** it is
   normalized, **Then** it is skipped in `repair` mode and raises in `strict` mode.
3. **Given** clean rows, **When** the storefront reads them, **Then** behavior is
   unchanged (parity).

---

### User Story 2 - A repair path (Priority: P1)

An operator can repair an existing storefront: dirty rows are rewritten to their
normalized form and the number repaired is reported.

**Independent Test**: Seed dirty rows, run the repair, and assert the rows are
normalized (or removed if unsalvageable).

**Acceptance Scenarios**:

1. **Given** a storefront with dirty rows, **When** the repair runs, **Then**
   fixable rows are rewritten and unsalvageable rows are removed and counted.

---

### User Story 3 - The normalization is measured (Priority: P2)

A keyless benchmark scores the normalizers against a labeled dirty-input set; the
gate fails below the threshold.

**Independent Test**: Run the benchmark and assert the accuracy meets the threshold.

**Acceptance Scenarios**:

1. **Given** the labeled set, **When** the benchmark runs, **Then** it reports the
   normalization accuracy and the gate enforces a minimum.

---

### Edge Cases

- **Missing value**: `None`/empty -> rejected or a defined default.
- **Negative price/stock**: rejected (not silently clamped).
- **Control characters / whitespace**: cleaned.
- **Conflicting duplicates**: the primary key wins (idempotent seeding).
- **Order with no valid items**: the order is invalid.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide pure normalizers: text cleaning, price and
  stock parsing, tag parsing, and product/order normalization.
- **FR-002**: The storefront MUST apply the normalizers at read boundaries;
  invalid rows MUST be skipped with a defined behavior in `repair` mode and MUST
  fail loud in `strict` mode (PB-1).
- **FR-003**: `data.quality` MUST select `repair` (default) or `strict`.
- **FR-004**: A repair path MUST rewrite a storefront to normalized rows and
  report what it fixed or removed (RD-2, traceable).
- **FR-005**: A keyless data-quality benchmark MUST score the normalizers against
  a labeled set, run in the gate, and be rendered in the report.
- **FR-006**: Clean data MUST be unchanged (parity).

### Key Entities

- **Normalizer**: a pure function from a raw value to a canonical value or a
  rejection.

## Real-World Coverage

- **Input distribution**: catalog/order rows from an external store; dirty inputs
  include currency symbols, thousands separators, "out of stock", padding,
  control characters, negatives, and missing fields.
- **Data quality**: this feature *is* the data-quality boundary — validate,
  normalize, or reject, with a defined reason; no silent assumptions.
- **Edge & failure modes**: missing/unparseable values are rejected; negatives
  rejected; duplicates resolved by key; an order with no valid items is invalid.
- **Scale envelope**: normalization is O(rows); a large catalog is out of scope
  (gap).
- **Degradation**: `strict` fails loud; `repair` skips and counts.
- **Change evidence**: the data-quality benchmark accuracy (see the change log).

## Observability

- The storefront reports how many rows were normalized or skipped; the benchmark
  writes a `data_quality` section to `evals/report.md`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The data-quality benchmark accuracy is **1.000** on the labeled set.
- **SC-002**: Clean rows are unchanged (parity).
- **SC-003**: `strict` raises on an invalid row; `repair` skips it and continues.
- **SC-004**: The repair rewrites fixable rows and removes unsalvageable ones.
- **SC-005**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Data Provenance & Licensing

- n/a: the data/corpus is authored in-repo; there is no external data source.

## Assumptions

- The storefront is the data boundary; there is no separate ingestion service.
- The labeled set is small and hand-curated; broader fuzzing is out of scope.
