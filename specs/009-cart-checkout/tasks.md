# Tasks: Cart and Checkout

**Feature**: `009-cart-checkout` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Tools

- [x] T001 `app/tools/cart.py`: `add_to_cart` (grounding, quantity), `view_cart`, payload builders
- [x] T002 `app/tools/cart.py`: `render_checkout` (summary; `charged: false`; no payment)
- [x] T003 `web/main.py`: `register_cart_tools(registry, storefront)`

## Phase 2 — Client rendering

- [x] T004 `lib/transport.ts`: `AgentDataTypes` + map `cart`/`checkout` components
- [x] T005 `components/app/cart-card.tsx`: cart + checkout card (items, totals)
- [x] T006 `App.tsx`: render `data-cart` / `data-checkout`

## Phase 3 — Tests + verify

- [x] T007 [P] Unit: `tests/unit/test_cart_tools.py` (grounding, increment, totals, no charge)
- [x] T008 [P] Integration: a turn that adds to the cart emits a `cart` component
- [x] T009 `scripts/ci.sh --fast`
- [x] T010 Browser checkpoint + `checkpoint.png` + `checkpoint.md`; update docs; PR

## Dependencies

- T001/T002 before T003/T007.
- T004/T005 before T006.
- T009/T010 last.
