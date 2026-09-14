# Browser checkpoint: 004-storefront-backend

Constitution SR-4 / SR-5. The catalog is user-visible, so a checkpoint is
recorded even though the feature is backend-only (WV-5).

## Card

```
Checkpoint: 004 storefront backend
URL:    http://127.0.0.1:8000
Steps:
  1. Ask for a tent.
  2. Confirm the search_products step completes and sources list the product.
Review:
  - [x] the tool reads from the configured backend (SQLite)
  - [x] behavior is unchanged (parity with 003)
  - [x] /readyz reports the storefront provider
Clauses: P4, PB-1, PB-2, RD-2, WV-5
Features: 004
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/004-storefront-backend/checkpoint.png`

| Check | Result |
| --- | --- |
| `search_products` step completes (`Completed`) | pass |
| Sources list the grounded product | pass |
| `/readyz` → `{"status":"ready","storefront":"sqlite"}` | pass |
| SQLite file created and seeded (5 rows) | pass |
| Idempotent seed: count stays 5 after restart | pass |
| Console errors | 0 |

## Notes

- Default provider is `sqlite` (`data/db/storefront.sqlite`); `memory` remains for
  keyless runs and tests.
- The tool's model-facing contract and the `products` UI component are unchanged
  (FR-007); only the data source changed.
- No new events; structured traces shipped in feature 007 (SL-2).
