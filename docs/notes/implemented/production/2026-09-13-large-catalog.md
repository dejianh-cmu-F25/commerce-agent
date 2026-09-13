# Agent Note: The large-catalog boundary is measured

Status: implemented (2026-09-13) — feature `041-large-catalog`

## Problem

The RW-2/SC-1 residual "large-catalog scale untested" was open. The storefront's
`search` reads, normalizes, and ranks the whole catalog per query (O(catalog)), so
catalog size is a real boundary — but it had never been measured.

## Alternatives considered

- **Measure an in-memory catalog.** A shortcut that skips the SQLite read and the
  normalization (feature 027) — not the real path. Rejected.
- **Measure the real SQLite storefront with 5,000 products.** Chosen.

## Decision

- **`evals/scale.py`** seeds a temporary SQLite storefront with 5,000 synthetic
  products and measures `search` at the target concurrency (budget p95 ≤ 50 ms).
- The result is rendered in the report, gated, and documented in `docs/scale.md`.

## Consequences

- The boundary is a number: search p95 is **~15 ms** over 5,000 products vs ~8 µs
  over 9 — the O(catalog) scan dominates. A SQL index (FTS or a filtered query)
  is the answer at volume.
- **Residual gaps**: catalogs >5,000 and concurrent writes are not measured;
  multi-tenant isolation is untested.
