# Tasks: Merchant Agent

**Feature**: `010-merchant-agent` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Port + adapter

- [x] T001 Add `Change` to `app/core/types.py`
- [x] T002 `MerchantBackend` protocol in `app/ports/merchant.py`
- [x] T003 `SqliteMerchant` in `app/adapters/merchant_sqlite.py` (stage/apply, validation)

## Phase 2 — Tools + API

- [x] T004 `app/tools/merchant.py`: `list_inventory`, `propose_price_change`, `propose_stock_change`, `list_pending_changes` (no approve)
- [x] T005 `web/main.py`: `build_merchant`; register tools; `GET /merchant/inventory`, `GET /merchant/changes`, `POST /merchant/changes/{id}/apply`

## Phase 3 — UI

- [x] T006 `lib/merchant.ts`: types + API helpers
- [x] T007 `components/app/merchant-view.tsx`: inventory + pending changes + Approve
- [x] T008 `App.tsx`: Merchant tab

## Phase 4 — Tests + verify

- [x] T009 [P] Unit: `tests/unit/test_merchant.py` (stage does not apply; apply once; validation)
- [x] T010 [P] Integration: `tests/integration/test_merchant_api.py` (inventory, changes, apply, 404)
- [x] T011 `scripts/ci.sh --fast`
- [x] T012 Browser checkpoint + docs + PR

## Dependencies

- T002/T003 before T004/T005/T009.
- T006/T007 before T008.
- T011/T012 last.
