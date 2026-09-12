# Browser checkpoint: 014-post-purchase

Constitution SR-4 / SR-5. Order status and returns are user-visible (chat cards),
so a checkpoint is recorded.

## Card

```
Checkpoint: 014 post-purchase care
URL:    http://127.0.0.1:8000
Steps:
  1. Ask "Where is my order?".
  2. Confirm list_orders shows the orders and get_order_status shows one order.
  3. Ask "I want to return the tent from order O-1001".
  4. Confirm a return card renders and states no refund is issued.
  5. Ask "I also want to return the backpack from order O-1002".
  6. Confirm the agent refuses (outside the return window) and no return card renders.
Review:
  - [x] orders list card + order detail card, grounded in the storefront
  - [x] in-window return renders a "Return requested" card (no refund, P3)
  - [x] out-of-window return is refused with the policy reason
  - [x] no console errors
Clauses: P3, P4, PB-1, PB-2, RD-1, RD-2, WV-3, WV-5, WV-6
Features: 014
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/014-post-purchase/checkpoint.png`

| Check | Result |
| --- | --- |
| `list_orders` renders the orders list (O-1003 shipped; O-1001/O-1002 delivered) | pass |
| `get_order_status` renders grounded status, items, and dates | pass |
| In-window return on O-1001 renders "Return requested" with "No refund is issued yet" | pass |
| Out-of-window return on O-1002 is refused with the window reason; no return card | pass |
| Tool spans recorded (`list_orders`, `get_order_status`, `start_return`) | pass |
| Console errors | 0 |

## Notes

- Orders are storefront state; demo orders seed per customer behind
  `storefront.seed_orders`. Return eligibility is a pure function of the order and
  `returns.window_days` (no model decision).
- `start_return` is render-only: it records a request and renders it; no refund,
  charge, or order mutation (P3). The card says a human/support confirms by email.
- For the out-of-window case the agent reasoned from `get_order_status` and
  declined without calling `start_return`; the tool-level refusal is covered by the
  `return_out_of_window` eval and the integration test.
