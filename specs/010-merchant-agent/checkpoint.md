# Browser checkpoint: 010-merchant-agent

Constitution SR-4 / SR-5. The merchant face is user-visible, so a checkpoint is
recorded.

## Card

```
Checkpoint: 010 merchant agent
URL:    http://127.0.0.1:8000
Steps:
  1. Open Merchant: the inventory is listed.
  2. In Chat, ask the operator agent to set P-101's price to $199.
  3. Back in Merchant: the staged change appears (189.00 -> 199.00).
  4. Approve it: the inventory updates and pending clears.
Review:
  - [x] inventory listed
  - [x] the agent stages a change (the product is unchanged until approval, P3)
  - [x] a human approves in the web; only then does the product update
Clauses: P3, PB-1, PB-2, PB-5, RD-2, WV-5
Features: 010
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/010-merchant-agent/checkpoint.png`

| Check | Result |
| --- | --- |
| Inventory listed (5 products) | pass |
| Agent proposed a change; staged (`189.00 → 199.00`) | pass |
| Approve button present and clicked | pass |
| Inventory updated to `$199.00` after approval | pass |
| Pending list cleared ("No pending changes.") | pass |
| Console errors | 0 |

## Notes

- The agent has **no** approval tool; only the web can apply a change (P3).
- Staging does not modify the product; `apply` is transactional and idempotent
  (no double-apply, RD-2).
- The merchant backend shares the storefront's SQLite file.
