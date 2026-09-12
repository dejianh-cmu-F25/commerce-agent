# Tasks: Session Persistence

**Feature**: `005-session-persistence` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Port + config

- [x] T001 Add `SessionRepository` protocol in `app/ports/session_store.py`
- [x] T002 Add `SessionSettings` + env overrides in `app/core/settings.py`
- [x] T003 [P] Add `config/settings.yaml` `session:` section

## Phase 2 — Providers

- [x] T004 Move the in-memory store to `app/adapters/session_memory.py` (`InMemorySessionStore`)
- [x] T005 `SqliteSessionStore` + event serialization in `app/adapters/session_sqlite.py`
- [x] T006 `build_session_store(settings)` in `web/main.py`

## Phase 3 — Consumer + API

- [x] T007 `web/main.py`: use the store in `/chat`; save after each turn
- [x] T008 `GET /sessions/{id}` returns derived messages (404 unknown)
- [x] T009 Remove/retire `web/sessions.py` (or re-export the memory store)

## Phase 4 — Tests

- [x] T010 [P] Unit: `tests/unit/test_session_memory.py`
- [x] T011 [P] Integration: `tests/integration/test_session_sqlite.py` (round-trip, idempotent save)
- [x] T012 Integration: `GET /sessions/{id}` 200 + 404 via `TestClient`

## Phase 5 — Verify & deliver

- [x] T013 `scripts/ci.sh --fast`
- [x] T014 Browser checkpoint + `checkpoint.png` + `checkpoint.md`
- [x] T015 Update `docs/architecture.md` (session store row)
- [x] T016 Commit and open the PR

## Dependencies

- T001 before T004/T005/T007.
- T005/T006 before T007.
- T010–T012 after T004/T005.
- T013–T016 last.
