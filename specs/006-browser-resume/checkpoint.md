# Browser checkpoint: 006-browser-resume

Constitution SR-4 / SR-5. The resume behavior is user-visible, so a checkpoint is
recorded.

## Card

```
Checkpoint: 006 browser resume
URL:    http://127.0.0.1:8000
Steps:
  1. Send a message; note the session id in localStorage.
  2. Reload the page: the exchange reappears.
  3. Send another message: it continues the same session.
  4. Click New chat: the transcript clears and the stored id is forgotten.
  5. Set a bogus stored id and reload: the app shows the empty state.
Review:
  - [x] reload restores the transcript
  - [x] the next message uses the same session_id
  - [x] New chat clears storage and the transcript
  - [x] a stale id is cleared with no error UI
Clauses: WV-1, WV-6, SL-1, RD-1
Features: 006
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/006-browser-resume/checkpoint.png`

| Check | Result |
| --- | --- |
| `session_id` persisted in `localStorage` on `SessionStarted` | pass |
| Reload restores the transcript (from `GET /sessions/{id}`) | pass |
| Message after reload carries the same `session_id` | pass |
| New chat clears storage and shows the empty state | pass |
| Stale id → cleared + empty state (no error UI) | pass |
| Console errors | 0 (the 404 shows as a network log only) |

## Notes

- History is text-only: tool steps are not reconstructed (spec 006 assumption).
- The transport reads/writes storage defensively; private mode degrades to a
  fresh session.
