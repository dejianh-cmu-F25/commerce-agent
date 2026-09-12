# Implementation Plan: Cart and Checkout

**Branch**: `009-cart-checkout` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-cart-checkout/spec.md`

## Summary

Add cart tools (`add_to_cart`, `view_cart`) that validate product ids against the
session (P4), read title/price from the storefront, and update the session cart;
render a `cart` UI component. Add `render_checkout` that renders a summary and
never charges (P3). Extend the client transport/App to render `cart`/`checkout`.

## Technical Context

**Language/Version**: Python 3.13 + TypeScript/React 19

**Primary Dependencies**: existing (tools/registry, storefront port, UIComponent seam)

**Storage**: the session cart (persisted by 005)

**Testing**: `pytest` (unit cart logic, integration turn); vitest (payload typing)

**Target Platform**: server + browser

**Project Type**: web service

**Performance Goals**: trivial (in-memory cart on the session)

**Constraints**: no payment code; only server-issued ids; no new dependencies

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes, harness disposes | `render_checkout` renders; never charges | PASS |
| P4 grounding | ids must be in the session; prices from the backend | PASS |
| P5 / PB-2 | tools registered via the existing registry; storefront injected | PASS |
| WV-3 | a new `cart` component in the registry | PASS |
| SL-1 | cart writes go through the tool result and the session log | PASS |
| RD-2 | adding the same product increments; no duplicate lines | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/009-cart-checkout/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/cart.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
app/tools/cart.py            # NEW: add_to_cart, view_cart, render_checkout
web/main.py                  # register_cart_tools(registry, storefront)
frontend/src/
├── lib/transport.ts         # map UIComponent cart/checkout -> data-cart/data-checkout
├── components/app/cart-card.tsx  # cart + checkout card
└── App.tsx                  # render data-cart / data-checkout
tests/unit/test_cart_tools.py
tests/integration/test_cart_turn.py
```

## Complexity Tracking

> No constitution violations; nothing to justify.
