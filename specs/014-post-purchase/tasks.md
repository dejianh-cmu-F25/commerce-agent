# Tasks: Post-Purchase Care

**Feature**: `014-post-purchase` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Types + config

- [x] T001 Add `Order`, `OrderItem`, `ReturnRequest` to `app/core/types.py`
- [x] T002 `ReturnsSettings` + `storefront.seed_orders` in `app/core/settings.py` and `config/settings.yaml`

## Phase 2 — Storefront orders

- [x] T003 `app/adapters/order_seed.py` (`demo_orders`)
- [x] T004 Extend `StorefrontBackend` port with `list_orders`, `get_order`
- [x] T005 `InMemoryStorefront`: orders + lazy idempotent seeding
- [x] T006 `SqliteStorefront`: orders/order_items tables + seeding

## Phase 3 — Tools + policy

- [x] T007 `app/returns/policy.py` (`return_eligibility`)
- [x] T008 `app/tools/orders.py` (`list_orders`, `get_order_status`, `start_return`)
- [x] T009 `web/main.py`: register order tools; pass `seed_orders`; prompt guidance

## Phase 4 — Frontend

- [x] T010 `transport.ts`: `orders` / `order` / `return` data parts
- [x] T011 `components/app/order-cards.tsx` + render in `App.tsx`

## Phase 5 — Tests + verify

- [x] T012 [P] Unit: `tests/unit/test_orders.py` (stores parity, seeding idempotent, eligibility)
- [x] T013 [P] Integration: `tests/integration/test_order_tools.py` (tools over the loop, grounding, gate)
- [x] T014 Evals: `order_status`, `start_return`, `return_out_of_window`
- [x] T015 `docs/architecture.md`; Agent Note
- [x] T016 `scripts/ci.sh --fast`; browser checkpoint; review; PR

## Dependencies

- T001 before T003–T008.
- T003/T004 before T005/T006.
- T007 before T008.
- T005/T006/T008 before T012–T014.
- T016 last.
