# Agent Note: Dirty data has defined behavior at the boundary

Status: implemented (2026-09-13) — feature `027-data-quality`

## Problem

The storefront read rows straight into the domain: `float(row["price"])`,
`int(row["stock"])`, `str(row["tags"]).split(",")`. Any upstream dirt — a price
with a currency symbol, a stock of `"out of stock"`, a null title, a control
character — either raised or silently produced garbage that could reach a
grounded answer. RW-2 was open: the project had no boundary validation, no
defined behavior for dirty data, and no repair path.

## Alternatives considered

- **Validate at write time only.** Misses existing rows and anything written by
  another writer. Rejected.
- **Clamp negatives to zero.** Hides a real data error. Rejected in favor of
  reject-and-count.
- **A third-party validation library (Pydantic already present).** Pydantic
  validates shape, not messy human text (`"$1,299.00"`); we still need the
  parsers. A schema layer on top would be extra surface for no gain. Rejected.
- **Pure normalizers applied at the read boundary + a repair script.** Chosen.

## Decision

- **`app/data/quality.py`** (stdlib only): `clean_text`, `parse_price`,
  `parse_stock`, `parse_tags`, `normalize_product`, `normalize_order`. Reject,
  don't clamp: an unparseable or negative value returns `None`.
- **The storefront normalizes on read.** `data.quality: repair` (default) skips
  an unusable row and counts it; `strict` raises (`PB-1`). Fixable values are
  normalized, so `"$1,299.00"` becomes `1299.00` and `"out of stock"` becomes `0`.
- **`scripts/repair_storefront.py`** rewrites/removes dirty rows and reports the
  counts; it is idempotent (`RD-2`).
- **Measured.** A 20-case labeled set (`evals/data_quality_set.py`) scores the
  normalizers; the gate enforces accuracy 1.0. The naive pre-change boundary
  scores 0.100 (2/20) on the same set, so the change log records **0.100 → 1.000**.

## Consequences

- A dirty row can no longer crash the agent or leak garbage; it is normalized,
  skipped, or fails loud by configuration.
- The labeled set is small and hand-curated; broader fuzzing and a large-catalog
  scale test remain open (see the spec's Scale envelope gap).
- No dependency was added.
