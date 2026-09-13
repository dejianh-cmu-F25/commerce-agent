# Feature Specification: Cart and Checkout

**Feature Branch**: `009-cart-checkout`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add cart tools (`add_to_cart`, `view_cart`) that accept only
server-issued product ids, update the session cart, and render a cart component;
add `render_checkout` that renders a summary and never charges (P3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add a grounded product to the cart (Priority: P1)

The customer asks to add a product the agent has already found. The tool accepts
the server-issued id, reads the current title and price from the storefront, and
updates the session cart.

**Why this priority**: The cart is the first write path; grounding (P4) matters
most here.

**Independent Test**: Add a known id and assert the cart line; add an unknown id
and assert it is rejected.

**Acceptance Scenarios**:

1. **Given** a product id the session has seen, **When** it is added, **Then** a
   cart line appears with the backend's title and price.
2. **Given** an id the session has not seen, **When** it is added, **Then** the
   tool returns an error and the cart is unchanged.
3. **Given** a product already in the cart, **When** it is added again, **Then**
   its quantity increases (no duplicate line).

---

### User Story 2 - View the cart (Priority: P1)

The customer can see the cart: items, quantities, line totals, and the total.

**Independent Test**: `view_cart` returns the current lines and total; the cart
component renders them.

**Acceptance Scenarios**:

1. **Given** a non-empty cart, **When** `view_cart` runs, **Then** it returns the
   lines and a server-computed total.
2. **Given** the cart, **When** it renders, **Then** a `cart` component shows the
   items and total.

---

### User Story 3 - Checkout renders, never charges (Priority: P1)

`render_checkout` produces a checkout summary. It **never** charges (P3): the
harness renders; payment is out of scope.

**Independent Test**: Run `render_checkout`; assert a summary is returned and no
charge/payment code path exists.

**Acceptance Scenarios**:

1. **Given** a non-empty cart, **When** `render_checkout` runs, **Then** a
   `checkout` component shows the items and total.
2. **Given** an empty cart, **When** `render_checkout` runs, **Then** it reports
   the cart is empty.

### Edge Cases

- Quantity ≤ 0 or non-numeric: clamped to 1.
- Adding an out-of-stock product: allowed (the cart is a proposal), but the line
  notes it is out of stock.
- The product no longer exists in the backend: reject (unknown id).
- The cart persists with the session (005) and is restored on resume.

## Requirements *(mandatory)*

- **FR-001**: `add_to_cart(product_id, quantity)` MUST reject ids not present in
  the session (P4) and MUST NOT change the cart on rejection.
- **FR-002**: Line title and unit price MUST come from the storefront backend, not
  from the model.
- **FR-003**: Adding an existing product MUST increment its quantity.
- **FR-004**: `view_cart()` MUST return the current lines and a server-computed
  total.
- **FR-005**: The cart MUST render through a `cart` UI component (WV-3).
- **FR-006**: `render_checkout()` MUST return a summary and MUST NOT charge (P3);
  no payment code exists.
- **FR-007**: The cart MUST persist with the session and be restored (RD).
- **FR-008**: Quantities MUST be clamped to ≥ 1.

### Key Entities

- **CartLine**: `product_id`, `title`, `quantity`, `unit_price` (existing).
- **Cart**: `items[]`, `total` (server-computed).
- **Checkout**: `items[]`, `total` (a render, not a charge).

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Cart | `add_to_cart` / `view_cart` | A cart card: items, quantities, line totals, total |
| Checkout | `render_checkout` | A checkout card: summary + total, with a "no payment" note |
| Empty cart | `view_cart` / `render_checkout` with no lines | "Your cart is empty." |
| Error | Unknown id | Inline tool error; cart unchanged |

## Web Acceptance

Ask "add the tent to my cart": a cart card shows the tent and the total. Ask
"checkout": a checkout card shows the summary; nothing is charged. Ask "what's in
my cart": the cart card is shown again.

## Observability

Cart turns emit the existing spans (007); tool spans show `add_to_cart` /
`render_checkout`. No new events.

## Success Criteria *(mandatory)*

- **SC-001**: A grounded product can be added; an ungrounded id is rejected.
- **SC-002**: The cart card renders items and a server-computed total.
- **SC-003**: `render_checkout` renders a summary and no charge occurs (no payment
  code; verified by inspection and the checkpoint).
- **SC-004**: The cart survives a reload (persisted with the session).

## Assumptions

- The cart is a proposal (P3): no inventory reservation, no payment.
- Prices are read from the storefront at add time; later price changes are not
  reconciled in this feature.
- The `cart` UI component reuses the 004 `UIComponent` seam.

## Real-World Coverage

- **Input distribution**: free-form add/checkout requests; ids must come from a search.
- **Data quality**: prices and titles come from the storefront, never the model (P4).
- **Edge & failure modes**: unknown product id → error; quantity clamped to ≥ 1; empty cart renders empty.
- **Scale envelope**: in-session cart; the system envelope is measured in `docs/scale.md`.
- **Degradation**: a storefront lookup failure is a tool error; the turn continues.
- **Change evidence**: checkout remains render-only (P3); behavior changes update the evals.
