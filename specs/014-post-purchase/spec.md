# Feature Specification: Post-Purchase Care

**Feature Branch**: `014-post-purchase`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Post-purchase care for the shopping agent: grounded order status and a
policy-gated, render-only return request. Orders live in the storefront system of
record; the agent reads them through tools and never invents an order. A return
is a proposal the harness validates against the configured policy and renders —
no refund is issued and no order state is changed (P3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check an order's status (Priority: P1)

A customer asks where their order is. The agent lists the customer's orders,
reads the chosen order, and answers with its grounded status, items, and dates.

**Why this priority**: Order status is the most common post-purchase question and
completes the consumer journey (discover → cart → checkout → post-purchase).

**Independent Test**: List orders for a customer, read one, and assert the
status/items come from the storefront and the order id is remembered as
server-issued.

**Acceptance Scenarios**:

1. **Given** a customer with orders, **When** they ask "where is my order?",
   **Then** the agent calls `list_orders` and shows the orders with their status.
2. **Given** a listed order, **When** the customer asks about it, **Then** the
   agent calls `get_order_status` and answers with grounded status, items, and
   dates.
3. **Given** an order id the session has not seen, **When** `get_order_status`
   runs, **Then** it is rejected (only server-issued ids, P4).

---

### User Story 2 - Start a return, policy-gated (Priority: P1)

A customer asks to return an item. The agent checks the order against the return
policy and either records a return request or explains why the item is not
returnable.

**Why this priority**: Returns are the highest-volume post-purchase action and a
clear place to show the harness enforcing policy (P3, P4).

**Independent Test**: Start a return for an in-window delivered order and assert a
return is rendered; start one for an out-of-window order and assert it is
rejected with a reason.

**Acceptance Scenarios**:

1. **Given** a delivered order inside the return window, **When** the customer
   asks to return an item on it, **Then** `start_return` records a return request
   and renders it, and no refund or order change occurs (P3).
2. **Given** a delivered order outside the return window, **When** a return is
   requested, **Then** the tool refuses with the policy reason and nothing is
   rendered as a return.
3. **Given** an order that is not delivered, **When** a return is requested,
   **Then** the tool refuses because the order has not arrived.
4. **Given** an order id the session has not seen, **When** `start_return` runs,
   **Then** it is rejected (P4).

---

### User Story 3 - Orders are config-selected and keyless (Priority: P2)

Orders come from the configured storefront provider with a keyless demo path; the
return window is configuration, validated at load.

**Independent Test**: Build the storefront with each provider and assert orders
parity; assert an invalid return window fails at load.

**Acceptance Scenarios**:

1. **Given** `storefront.provider: memory`, **When** orders are listed, **Then**
   the keyless provider returns the same orders as SQLite.
2. **Given** `returns.window_days`, **When** the app starts, **Then** the value
   is validated and used for eligibility.

---

### Edge Cases

- **No customer identity**: with no customer id, orders cannot be listed; the
  agent says it cannot find orders rather than inventing one.
- **Unknown order id**: `get_order_status`/`start_return` reject ids the session
  has not seen (P4).
- **Empty order list**: the agent says there are no orders on this account.
- **No `delivered_at`**: an order that is not delivered is never returnable.
- **Storefront error**: an order lookup failure surfaces as a tool error and does
  not end the turn (RD-1).
- **Reload**: order/return cards are not reconstructed from history (history is
  text-only), consistent with cart and tool steps.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The storefront capability MUST expose the customer's orders:
  `list_orders(customer_id)` and `get_order(customer_id, order_id)`.
- **FR-002**: Orders MUST be readable from both the keyless in-memory provider and
  the SQLite provider, with parity; demo orders MUST be seeded idempotently per
  customer behind a config switch (RD-2, P8).
- **FR-003**: The system MUST expose a `list_orders` tool that returns the
  customer's orders and remembers their ids as server-issued (P4).
- **FR-004**: The system MUST expose a `get_order_status` tool that accepts only
  ids the session has seen and returns grounded status, items, and dates.
- **FR-005**: The system MUST expose a `start_return` tool that accepts only ids
  the session has seen and validates eligibility against the configured return
  window.
- **FR-006**: Return eligibility MUST require: the order exists, is `delivered`,
  was delivered within `returns.window_days`, and contains the requested item.
- **FR-007**: `start_return` MUST be render-only: it records a return request and
  renders it, and MUST NOT issue a refund, change the order, or change inventory
  (P3).
- **FR-008**: The return window MUST come from configuration and be validated at
  load; an invalid value MUST fail loud (PB-1).
- **FR-009**: Order and return outcomes MUST render as distinct UI components
  (orders list, order detail, return confirmation) via the component contract
  (WV-3).
- **FR-010**: Order lookups and the return decision MUST emit structured spans
  under the turn's `trace_id` (SL-2, OB-1).

### Key Entities *(include if feature involves data)*

- **Order**: a customer's purchase. Attributes: a server-issued id, the owning
  customer id, a status (`processing` | `shipped` | `delivered` | `cancelled`),
  placed/delivered dates, and line items.
- **OrderItem**: a line on an order (product id, title, quantity, unit price).
- **ReturnRequest**: a customer's request to return an item. Attributes: the
  order id, the item, the status (`requested`), and when it was requested. It is
  a proposal; no refund is implied.

## UI Requirements

Order and return outcomes render as cards inside the chat transcript, alongside
the existing product, cart, and checkout cards. There is no new tab.

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | The customer has no orders | The agent says so in text; no card is rendered |
| Loading / Streaming | A tool call is in flight | The tool step shows running, then its result (existing step behavior) |
| Success | Orders listed / order read / return recorded | An orders list card, an order detail card (status, items, dates, returnable), or a return confirmation card stating no refund is issued yet |
| Error | Unknown id, not delivered, or out of window | An inline tool step marked error and the agent's explanation; no card |
| Disabled | Not applicable to these read-only cards | — |

### Accessibility

- [ ] Cards use semantic lists/headings and are keyboard-scrollable; no interactive control is required.
- [ ] Status is conveyed by text, not color alone.
- [ ] Motion respects `prefers-reduced-motion`.
- [ ] Text remains ≥16px where it is input; card text wraps without clipping.

### Responsive & Theme

- [ ] Cards sit in the app's fluid column (`min(80rem, 92%)`); wide item rows wrap or scroll inside the card, with no page-level horizontal scroll from 320px up.
- [ ] Theme follows `prefers-color-scheme`.

## Web Acceptance

- Asking "where is my order?" shows the customer's orders and, on follow-up, a
  grounded order detail card.
- Asking to return an item on a delivered, in-window order shows a return
  confirmation that states no refund is issued yet.
- Asking to return an out-of-window or undelivered order shows a clear refusal
  with the policy reason and no return card.

## Observability

- Order tool calls emit `tool` spans (existing); the return decision emits its
  outcome (eligible / refused, with the reason) in the tool span attributes.
- `list_orders`, `get_order_status`, and `start_return` are visible in the Trace
  Viewer timeline like any other tool.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Order status answers are grounded: 100% of gold scenarios answer
  from a storefront order, never an invented one.
- **SC-002**: Returns are policy-correct: in-window delivered orders are accepted;
  out-of-window or undelivered orders are refused, in 100% of gold scenarios.
- **SC-003**: Memory and SQLite providers return the same orders for the same
  customer (parity).
- **SC-004**: No refund, charge, or order mutation occurs on `start_return` (P3).
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes with the feature enabled.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Human-in-the-Loop

- n/a: this feature performs no state-changing action (read-only or a proposal).

## Assumptions

- Orders are seeded demo fixtures for a keyless, interview-grade demo; there is
  no real order placement (checkout is render-only by design).
- Demo order ids are per-customer (`O-1001`, …); lookups are scoped by customer.
- The machine-readable return window lives in config; the human-readable policy
  lives in `config/knowledge/returns.md` and must stay in sync.
- Returns are requests, not refunds; fulfillment is out of scope.
- A customer id (feature 013) identifies the order owner; without one, orders
  are unavailable.

## Real-World Coverage

- **Input distribution**: order-status and return requests; ids must be
  server-issued (P4).
- **Data quality**: orders come from the storefront; demo orders seed idempotently.
- **Edge & failure modes**: unknown order id → error; out-of-window or
  undelivered returns are refused with a reason.
- **Scale envelope**: a small per-customer order history; the system envelope is measured in `docs/scale.md`.
- **Degradation**: an order lookup failure is a tool error; the turn continues.
- **Change evidence**: behavior changes update the gold scenarios and `specs/RESULTS.md`.
