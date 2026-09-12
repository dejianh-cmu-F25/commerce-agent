# Browser checkpoint: 005-session-persistence

Constitution SR-4 / SR-5. The chat is user-visible and sessions are now durable,
so a checkpoint is recorded.

## Card

```
Checkpoint: 005 session persistence
URL:    http://127.0.0.1:8000
Steps:
  1. Send a message.
  2. Confirm the turn completes as before (parity).
  3. Fetch the session: GET /sessions/{id}.
  4. Restart the app and fetch the same id again.
Review:
  - [x] chat behavior unchanged
  - [x] the session is saved and retrievable by id
  - [x] the session survives a restart
Clauses: SL-1, PB-1, PB-2, RD-2, P4, WV-5
Features: 005
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/005-session-persistence/checkpoint.png`

| Check | Result |
| --- | --- |
| `search_products` completes; sources render; 0 console errors | pass |
| `GET /sessions/{id}` returns derived messages (user/assistant/tool) | pass |
| Unknown id → 404 | pass |
| Session survives a process restart (`GET` still 200) | pass |
| `derive_messages` identical before/after save+load (integration test) | pass |
| Idempotent save (no duplicate events) | pass |

## Notes

- Store is `sqlite` by default (`data/db/sessions.sqlite`); `memory` remains for
  keyless runs and tests.
- The web app is now built via a factory (`uvicorn web.main:create_app --factory`)
  so importing the module no longer needs an API key; Docker and `serve.sh` use
  the same command.
- Client-side transcript rehydration after a browser reload is a follow-up; the
  server-side resume is exposed via `GET /sessions/{id}`.
