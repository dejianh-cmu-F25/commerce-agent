# Research: Browser Resume

## D1. Where to store the session id

**Decision**: `localStorage` under `commerce-agent.session`, read at module load
and written on `SessionStarted`. Access is wrapped so an unavailable storage
(private mode) degrades to a fresh session.

**Rationale**: Simple, survives reloads, no cookies/URLs.

**Alternatives considered**: a cookie (rejected: sent to the server needlessly);
a URL param (rejected: ugly, shareable links not desired).

## D2. Rehydration source

**Decision**: `GET /sessions/{id}` (from 005) returns derived messages; the client
maps them to AI SDK `UIMessage`s and calls `setMessages`.

**Rationale**: The server owns the log (SL-1); the client only renders.

**Alternatives considered**: replaying raw events (rejected: the endpoint already
derives the model view).

## D3. Text-only history

**Decision**: Rehydrate user and assistant **text** only; skip tool messages and
tool calls.

**Rationale**: Keeps the mapping simple and type-safe; the final answers are what
the user reads. Reconstructing tool parts is a possible follow-up.

**Alternatives considered**: reconstruct `tool-*` parts (deferred: more type
surface and risk for little demo value).

## D4. Stale or failing history

**Decision**: A 404 clears the stored id and starts fresh; any other failure shows
the empty state but leaves the composer usable (RD-1).

**Rationale**: Never block the user on a resume failure.

## D5. New chat

**Decision**: A header action clears the stored id, resets the transport, and
`setMessages([])`.

**Rationale**: Gives the user an explicit way to start over.
