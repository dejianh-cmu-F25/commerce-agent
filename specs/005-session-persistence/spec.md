# Feature Specification: Session Persistence

**Feature Branch**: `005-session-persistence`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Persist the session log to SQLite so conversations survive restarts and
can be resumed by `session_id`, with `derive_messages` producing identical
messages after reload.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversations survive a restart (Priority: P1)

The agent's session log is durable. After the process restarts, a session can be
reloaded and its model messages are byte-identical to before (SL-1).

**Why this priority**: The log is the source of truth; if it is lost on restart,
reproducibility, evaluation, and resume are impossible.

**Independent Test**: Append events, save, reload into a fresh store, and assert
`derive_messages(loaded) == derive_messages(original)`.

**Acceptance Scenarios**:

1. **Given** a session with a user message, a tool call, and an assistant reply,
   **When** it is saved and reloaded, **Then** the derived messages are identical.
2. **Given** a reloaded session, **When** a new turn runs, **Then** the model sees
   the prior context (the conversation continues).

---

### User Story 2 - The store is configurable (Priority: P1)

The operator chooses the session store in configuration; an unknown choice fails
loud at load.

**Why this priority**: PB-1 / PB-2, and tests need an in-memory store.

**Independent Test**: Load settings with each provider and assert the factory
returns the matching store.

**Acceptance Scenarios**:

1. **Given** `session.store: memory`, **When** the app starts, **Then** sessions
   live for the process only.
2. **Given** `session.store: sqlite`, **When** the app starts, **Then** sessions
   are persisted to the configured path.

---

### User Story 3 - Sessions are inspectable (Priority: P2)

A session can be fetched over HTTP by id, returning its derived messages, so
resume/debug is possible from the web surface (WV-5).

**Independent Test**: Run a turn, then `GET /sessions/{id}`; assert the messages
match the session.

**Acceptance Scenarios**:

1. **Given** a completed turn, **When** `GET /sessions/{id}` is called, **Then**
   the derived messages are returned.
2. **Given** an unknown id, **When** it is requested, **Then** the response is 404.

### Edge Cases

- Unknown `session_id` on `/chat`: a new session is created (current behavior).
- The SQLite path is unwritable: fail loud at startup.
- Saving twice with no new events: no duplicates (idempotent, RD-2).
- A corrupt stored row: skip/fail loud rather than silently dropping the log.

## Requirements *(mandatory)*

- **FR-001**: A `SessionRepository` port MUST define `create`, `get`,
  `get_or_create`, and `save`.
- **FR-002**: The port MUST have at least two providers: in-memory and SQLite.
- **FR-003**: The provider MUST be selected by `config/settings.yaml` and
  validated; an unknown value MUST fail loud at load (PB-1).
- **FR-004**: The stored log MUST round-trip exactly: `derive_messages(loaded)`
  MUST equal `derive_messages(original)` (SL-1).
- **FR-005**: Events MUST be append-only: existing events are never rewritten and
  keep their order (stable sequence).
- **FR-006**: Provenance and cart MUST be restored with the session (P4).
- **FR-007**: The web layer MUST persist the session after each turn and MUST use
  the configured store.
- **FR-008**: `GET /sessions/{id}` MUST return the session's derived messages, or
  404 for an unknown id.
- **FR-009**: `save` MUST be idempotent (no duplicate events) (RD-2).
- **FR-010**: The in-memory store MUST keep the current behavior for keyless runs
  (P8).

### Key Entities

- **SessionRepository**: the capability (create, get, get_or_create, save).
- **SessionRecord**: the persisted form of `Session` (events, provenance, cart).
- **SessionSettings**: `store` (`memory` | `sqlite`), `sqlite_path`.

## UI States *(convention, WV-6)*

The browser surface is unchanged; the chat states are as in 003. Persistence is
observable through `GET /sessions/{id}`.

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | Load, no messages | Unchanged from 003 |
| Streaming | Message sent | Unchanged; the session is saved after the turn |
| Success | Turn ends | Unchanged |
| Error | Failure | Unchanged |

## Web Acceptance *(convention, WV-1)*

Open `/`, send a message. After the turn, `GET /sessions/{id}` returns the
messages. Restart the app and request the same id: the messages are still there.

## Observability *(convention, WV-1)*

No new events; structured traces arrive with feature 080 (SL-2).

## Success Criteria *(mandatory)*

- **SC-001**: `derive_messages` is identical before and after a save/load cycle.
- **SC-002**: A session survives a process restart (SQLite) and is retrievable by
  id.
- **SC-003**: Unit tests cover the in-memory store; integration tests cover the
  SQLite store (round-trip, idempotent save, 404 path via the API).
- **SC-004**: Switching `session.store` changes the provider with no code change.

## Assumptions

- Client-side transcript rehydration after a browser reload is a follow-up; this
  feature persists server-side and exposes resume via `GET /sessions/{id}`.
- The event types are those of 001 (`UserMessage`, `AssistantMessage`,
  `ToolResultEvent`); new event types must extend the serialization.
- Cart is persisted but empty until the cart feature lands.
