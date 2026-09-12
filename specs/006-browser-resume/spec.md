# Feature Specification: Browser Resume

**Feature Branch**: `006-browser-resume`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Persist the session id in the browser and rehydrate the transcript from
`GET /sessions/{id}` on load so a page reload resumes the conversation; add a
New chat action.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reload resumes the conversation (Priority: P1)

A customer reloads the page and sees their previous messages again; the next
message continues the same server-side session (the agent remembers context).

**Why this priority**: 005 persists the log server-side; without client resume the
user cannot reach it, so the feature is invisible.

**Independent Test**: Send a message, reload, and assert the transcript is
restored and a new message continues the same session.

**Acceptance Scenarios**:

1. **Given** a conversation, **When** the page reloads, **Then** the previous
   messages are shown again.
2. **Given** a reloaded conversation, **When** the customer sends a new message,
   **Then** it is sent with the same `session_id` and the agent uses prior context.

---

### User Story 2 - New chat starts fresh (Priority: P2)

A customer can start a new conversation, discarding the stored session.

**Independent Test**: Click New chat; assert the transcript clears and the next
message creates a new session.

**Acceptance Scenarios**:

1. **Given** a resumed conversation, **When** the customer clicks New chat,
   **Then** the transcript clears and the stored session id is forgotten.

---

### User Story 3 - A stale session id is handled gracefully (Priority: P2)

If the stored session no longer exists, the app starts a fresh conversation
instead of showing an error.

**Independent Test**: Store an unknown session id, reload, and assert the app is
usable (empty transcript) and the stale id is cleared.

**Acceptance Scenarios**:

1. **Given** an unknown stored id, **When** the page loads, **Then** the transcript
   is empty and the id is cleared.

### Edge Cases

- `GET /sessions/{id}` fails (network/500): show the empty state; do not block the
  composer.
- Storage unavailable (private mode): behave as a fresh session.
- Very long history: rehydration is one request; rendering is bounded by the
  transcript.

## Requirements *(mandatory)*

- **FR-001**: The client MUST persist the `session_id` (browser storage) when the
  server sends `SessionStarted`.
- **FR-002**: On load, if a stored id exists, the client MUST fetch
  `GET /sessions/{id}` and rehydrate the transcript via `setMessages`.
- **FR-003**: A 404 MUST clear the stored id and start fresh (no error UI).
- **FR-004**: Sending after a reload MUST continue the same session.
- **FR-005**: A New chat action MUST clear the stored id and the transcript.
- **FR-006**: Rehydration MUST render user and assistant text; tool steps MAY be
  omitted (documented).
- **FR-007**: A failure to load history MUST NOT prevent sending a new message.

### Key Entities

- **StoredSession**: the `session_id` kept in browser storage.
- **Resume mapping**: server messages → AI SDK `UIMessage` parts.

## UI States *(convention, WV-6)*

| State | Trigger | What the user sees |
| --- | --- | --- |
| Resuming | Load with a stored session id | Brief empty transcript until history loads; composer available |
| Empty | No stored id, or cleared | Suggestion chips (as in 003) |
| Streaming / Success / Error | As in 003 | Unchanged |

## Web Acceptance *(convention, WV-1)*

Send "I need a tent under $250", reload the page: the exchange reappears. Send
another message: the agent answers with prior context (same `session_id`). Click
New chat: the transcript clears and a new session starts.

## Observability *(convention, WV-1)*

No new events; structured traces arrive with feature 080 (SL-2).

## Success Criteria *(mandatory)*

- **SC-001**: After a reload, the previous messages are shown again.
- **SC-002**: A message sent after a reload carries the same `session_id`.
- **SC-003**: New chat clears storage and the transcript.
- **SC-004**: An unknown stored id yields a usable empty state (no error).

## Assumptions

- 005 provides `GET /sessions/{id}`.
- The AI SDK `useChat` exposes `setMessages` for rehydration.
- Tool steps are not reconstructed on resume (text-only history) — a documented
  limitation.
