# Implementation Plan: Session Persistence

**Branch**: `005-session-persistence` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-session-persistence/spec.md`

## Summary

Introduce a `SessionRepository` port with in-memory and SQLite providers,
config-selected, and use it in the web layer so a session log survives restarts
and resumes by id. The stored log round-trips exactly (SL-1); events are
append-only (RD-2). Add `GET /sessions/{id}` returning derived messages (WV-5).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib `sqlite3`, `json`; existing `pydantic` settings

**Storage**: SQLite under `data/db/` (embedded, DP-6)

**Testing**: `pytest` — unit (memory store), integration (SQLite round-trip +
API 404)

**Target Platform**: server (Docker + local)

**Project Type**: web service (state persistence)

**Performance Goals**: tiny logs; one save per turn

**Constraints**: exact round-trip of the log; append-only; fail loud on bad config

**Scale/Scope**: demo sessions; the seam is meant to be replaced by a real store

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SL-1 model-visible means logged | stored log round-trips; `derive_messages` unchanged | PASS |
| PB-1 config as contract | `session.store` validated; fail loud | PASS |
| PB-2 capability seam | Definition (port) + Providers (memory, sqlite) + Consumer (web) | PASS |
| PB-3 explicit boundaries | factory resolves provider explicitly | PASS |
| PB-5 validate at boundaries | validate config; validate stored rows | PASS |
| P4 grounding | provenance restored with the session | PASS |
| P6 simplicity | stdlib sqlite3; JSON payloads | PASS |
| RD-2 idempotent data | append-only by `(session_id, seq)`; no duplicates | PASS |
| P8 reproducible | memory provider keeps the keyless path | PASS |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-session-persistence/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/session-store.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
app/
├── core/settings.py         # + SessionSettings
├── ports/
│   └── session_store.py     # NEW: SessionRepository protocol
├── adapters/
│   ├── session_memory.py    # NEW: InMemorySessionStore
│   └── session_sqlite.py    # NEW: SqliteSessionStore (+ serialization)
web/
├── sessions.py              # keep SessionStore as the memory adapter? (moved)
└── main.py                  # build_session_store(settings); GET /sessions/{id}
tests/
├── unit/test_session_memory.py
└── integration/test_session_sqlite.py
```

**Structure Decision**: Follow the ports/adapters layering. The existing
`web/sessions.py` store moves to `app/adapters/session_memory.py` as the memory
provider; the factory lives at the composition root (`web/main.py`).

## Complexity Tracking

> No constitution violations; nothing to justify.
