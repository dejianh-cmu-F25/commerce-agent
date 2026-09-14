# Browser checkpoint: 013-customer-memory

Constitution SR-4 / SR-5. Customer memory is user-visible (a Memory view and
cross-session answers), so a checkpoint is recorded.

## Card

```
Checkpoint: 013 customer memory
URL:    http://127.0.0.1:8000
Steps:
  1. Say "I usually wear size M and I'm allergic to wool".
  2. Open the Memory tab; confirm the two facts are listed.
  3. Start a New chat and ask "What do you remember about me?".
  4. Forget one fact in the Memory tab; confirm it is removed.
Review:
  - [x] the two durable facts are stored (Profile: Wears size M; Constraint: Avoids wool)
  - [x] a later session recalls them without being told again
  - [x] a forgotten fact disappears from the view
  - [x] no console errors
Clauses: P3, P4, SL-1, SL-2, RD-1, RD-2, WV-5, WV-6
Features: 013
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/013-customer-memory/checkpoint.png`

| Check | Result |
| --- | --- |
| Durable facts extracted from the customer's text | pass |
| Memory view lists the facts with kind and learned date | pass |
| New chat recalls the facts ("You wear size M and you avoid wool.") | pass |
| Forgetting a fact removes it from the view | pass |
| `memory` spans emitted (`extract` stored=2; `recall` recalled=2) | pass |
| Console errors | 0 |

## Notes

- Extraction is deterministic and keyless (P8); no model call, no new
  dependency. Facts come only from the customer's own words (P4).
- Recalled facts are recorded as a `MemoryNote` in the session log, so the model
  context stays reconstructable (SL-1); a session with no facts is unchanged.
- The `memory` span redacts the customer id to 8 characters (OB-5).
- Identity is an opaque browser id (`commerce-agent.customer`), not auth.
- The first attempt hit a stale uvicorn still bound to :8000 (its `/readyz`
  lacked the `memory` field); restarted the server and re-ran. No product bug.
