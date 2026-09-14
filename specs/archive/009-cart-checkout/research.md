# Research: Cart and Checkout

## D1. Where cart state lives

**Decision**: on the `Session` (`session.cart`), which 005 already persists and
restores. Tools mutate it; the loop forwards the rendered component.

**Rationale**: the cart is session state; persistence and resume come for free.

## D2. Grounding the add (P4)

**Decision**: `add_to_cart` requires `session.knows(product_id)`; title and price
are read from the storefront (`storefront.get`), never from the model.

**Rationale**: the model proposes an id; the harness disposes with server data.

## D3. Rendering via the UIComponent seam

**Decision**: tools return `ToolResult(component="cart" | "checkout", payload=…)`;
the loop already forwards a tool-declared `UIComponent` (004). The client maps the
component name to a `data-*` part.

**Rationale**: reuse the existing seam; no new event types.

## D4. Checkout never charges (P3)

**Decision**: `render_checkout` computes a summary and returns it; there is no
payment code and no order is placed.

**Rationale**: P3; the constitution forbids charging.

## D5. Quantity handling

**Decision**: clamp to ≥ 1; adding an existing product increments the line.

**Rationale**: RD-2 (no duplicate lines) and simple, predictable behavior.
