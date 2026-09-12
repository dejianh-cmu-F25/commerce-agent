# Agent Note: Post-purchase orders are storefront state; returns are render-only

Status: implemented (2026-09-13) — feature `014-post-purchase`

## Problem

The consumer journey stopped at checkout. Post-purchase care (order status and
returns) raises cross-cutting questions that outlive the feature:

1. **Where do orders live?** Checkout is render-only (P3), so no order is ever
   placed by the agent. The demo still needs orders to answer "where is my
   order?".
2. **Who decides a return?** A return touches money and inventory; letting the
   model decide eligibility would put an irreversible action behind a
   non-deterministic step.
3. **What is a return, if the agent never charges?** It cannot be a refund; it
   must be a request the store acts on out of band.

## Alternatives considered

- **A new `OrderBackend` port.** Clean separation, but orders and products share
  one system of record and one provider selection. A second seam with no second
  implementation adds ceremony (PB-2). Rejected: extend `StorefrontBackend`.
- **The model decides return eligibility.** Flexible for edge cases, but
  non-deterministic and ungrounded for a policy decision. Rejected in favor of a
  pure function over the order and the configured window (HR-4).
- **Seed orders at startup for a fixed demo customer.** Simple, but the browser's
  customer id is dynamic (feature 013), so no browser would see orders. Rejected.
- **Generate globally-unique order ids at seed time.** Realistic, but the eval
  scripts the model's tool calls with fixed arguments and cannot know random ids.
  Rejected in favor of fixed per-customer demo ids (`O-1001`…), scoped by
  customer on lookup.
- **Persist returns as derived session state (like the cart).** Unnecessary: the
  tool result is already durable in the session log, and there is no "view
  returns" tool. Rejected as over-building.

## Decision

- **Orders are part of the storefront capability.** `StorefrontBackend` gains
  `list_orders(customer_id)` and `get_order(customer_id, order_id)`; the memory
  and SQLite providers both implement them with parity.
- **Demo orders seed lazily, idempotently, per customer**, behind
  `storefront.seed_orders`. This is fixture data, analogous to the catalog seed,
  and the only place a read seeds — documented and config-gated.
- **Return eligibility is computational.** `app/returns/policy.py` is a pure
  function of the order, the item, and `returns.window_days`; it returns a reason
  the tool renders. The model never decides.
- **A return is render-only.** `start_return` records a request in its result
  (durable in the session log) and renders a card stating no refund is issued;
  it never refunds, charges, or mutates the order (P3).

## Consequences

- Order answers are grounded: the model must call `list_orders` first, and only
  ids the storefront returned are accepted (P4).
- The return window has two representations — config (machine) and
  `config/knowledge/returns.md` (human) — that must stay in sync; the config
  value is authoritative for eligibility.
- Demo order ids are per-customer, not globally unique. This is a demo
  simplification recorded here; a real system would issue globally unique ids.
- Fulfillment (processing a return, refunding, restocking) is out of scope; the
  card says so.
