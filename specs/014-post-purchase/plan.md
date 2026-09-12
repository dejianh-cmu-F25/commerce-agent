# Implementation Plan: Post-Purchase Care

**Branch**: `014-post-purchase` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/014-post-purchase/spec.md`

## Summary

Extend the storefront capability with customer orders (memory + SQLite providers,
idempotent per-customer demo seeding behind a config switch) and add three tools:
`list_orders`, `get_order_status`, and a policy-gated, render-only `start_return`.
Return eligibility is computed from the order plus `returns.window_days`
(config-as-policy). Orders and returns render as new chat cards. No new
dependencies; no refund or order mutation.

## Technical Context

**Language/Version**: Python 3.13; React 19 + TypeScript (frontend)

**Primary Dependencies**: Python stdlib only (`sqlite3`, `datetime`); existing
frontend stack

**Storage**: orders in the storefront (SQLite `storefront.sqlite` or in-memory)

**Testing**: `pytest` (unit: order stores, eligibility; integration: the tools
over the loop); eval scenarios for status and the return gate

**Target Platform**: server + browser

**Performance Goals**: tiny order set per customer; O(items) eligibility

**Constraints**: keyless; grounded (orders only from the storefront, P4);
render-only returns (P3); fail loud on bad config (PB-1)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes, harness disposes | `start_return` records a request only; no refund/charge/order mutation | PASS |
| P4 grounding | order status/items/dates and eligibility come from storefront results; only server-issued ids accepted | PASS |
| P5 / PB-2 capability seam | orders are part of the `StorefrontBackend` definition; two providers | PASS |
| PB-1 config as contract | `storefront.seed_orders`, `returns.window_days` validated | PASS |
| PB-4 prompts external | no new model step; prompt file only | PASS |
| SL-1 model-visible means logged | tool results are session-log events; no out-of-band context | PASS |
| SL-2 / OB-1 | tool spans carry the return decision | PASS |
| P6 / P8 | stdlib only; keyless demo orders | PASS |
| RD-1 resilience | lookup failure is a tool error, never a turn failure | PASS |
| RD-2 idempotent data | demo seeding uses `INSERT OR IGNORE`; listing twice is stable | PASS |
| WV-3 / WV-5 | new `orders` / `order` / `return` components; reachable from chat | PASS |
| HR-11 extension point | orders attach to the storefront seam; documented | PASS |

## Project Structure

```text
app/
├── core/types.py             # + Order, OrderItem, ReturnRequest
├── core/settings.py          # + storefront.seed_orders, ReturnsSettings
├── ports/storefront.py       # + list_orders, get_order
├── adapters/order_seed.py    # NEW: demo orders per customer
├── adapters/storefront_memory.py   # + orders
├── adapters/storefront_sqlite.py   # + orders tables
├── returns/policy.py         # NEW: return_eligibility(order, window_days, now)
└── tools/orders.py           # NEW: list_orders, get_order_status, start_return
web/main.py                   # register order tools; seed_orders in build_storefront
config/settings.yaml          # storefront.seed_orders; returns.window_days
config/prompts/system.md      # post-purchase guidance
frontend/src/
├── lib/transport.ts          # orders/order/return data parts
├── components/app/order-cards.tsx  # NEW
└── App.tsx                   # render the new cards
tests/unit/test_orders.py
tests/integration/test_order_tools.py
evals/scenarios.py            # + order_status, start_return, return_out_of_window
docs/architecture.md          # orders extension point
docs/notes/implemented/architecture/...-post-purchase.md
```

## Design decisions

- **Orders are storefront state, not a new port.** The storefront is the system
  of record for products and now orders; adding methods keeps one seam (PB-2).
- **Demo orders seed lazily and idempotently per customer.** The browser's
  customer id is dynamic, so seeding happens on first `list_orders` for a
  customer, behind `storefront.seed_orders`. This is fixture data, analogous to
  the catalog seed, and is documented as such.
- **Return eligibility is a pure function of order + config.** `returns.window_days`
  is the machine policy; the tool renders the decision and reason. No LLM decides
  eligibility (computational control, HR-4).
- **A return is render-only.** It records a request in the tool result (which is
  already durable in the session log) and renders it; no refund, no order change
  (P3). Fulfillment is out of scope.

## Complexity Tracking

> No constitution violations. The storefront port grows two read methods; the
> demo seeding is config-gated and documented. No new dependency.
