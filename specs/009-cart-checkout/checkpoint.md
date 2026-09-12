# Browser checkpoint: 009-cart-checkout

Constitution SR-4 / SR-5. The cart and checkout are user-visible, so a checkpoint
is recorded.

## Card

```
Checkpoint: 009 cart and checkout
URL:    http://127.0.0.1:8000
Steps:
  1. Ask for a tent and to add it to the cart.
  2. Ask to show the checkout summary.
Review:
  - [x] a cart card shows the item and total
  - [x] render_checkout renders a summary
  - [x] nothing is charged (P3)
Clauses: P3, P4, WV-1, WV-3, RD-2
Features: 009
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/009-cart-checkout/checkpoint.png`

| Check | Result |
| --- | --- |
| Cart card renders (`2-Person Tent ×1`, `$189.00`) | pass |
| `render_checkout` step completes | pass |
| Checkout card renders with the "No payment is taken" note | pass |
| Assistant summary states nothing was charged / no order placed | pass |
| Console errors | 0 |

## Notes

- `add_to_cart` rejects ids the session has not seen (P4); prices come from the
  storefront, not the model.
- The cart persists with the session (005) and is restored on resume.
- Checkpoint harness caveat: sending a new message while the previous `/chat`
  stream is still open aborts the previous turn (standard chat behavior). The
  checkpoint waits for the request to finish between turns.
