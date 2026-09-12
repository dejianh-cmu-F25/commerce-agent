# Contract: Browser resume

## Storage

| Key | Written when | Cleared when |
| --- | --- | --- |
| `commerce-agent.session` | `SessionStarted` arrives | New chat; a 404 from `GET /sessions/{id}` |

Access is guarded: if storage throws (private mode), the app behaves as a fresh
session.

## Transport (`frontend/src/lib/transport.ts`)

- Reads the stored id at construction and sends it as `session_id` on the first
  request after a reload.
- Writes the id when `SessionStarted` is received.
- `getSessionId(): string | null` and `reset(): void` are exposed.

## Resume mapping (`frontend/src/lib/resume.ts`)

```ts
rehydrateMessages(messages: ServerMessage[]): AgentUIMessage[]
```

- `user` → one text part.
- `assistant` with non-empty `content` → one text part; empty content is skipped.
- `tool` → skipped.
- Ids are fresh (`crypto.randomUUID`).

## App behavior (`frontend/src/App.tsx`)

- On mount: if a stored id exists, `fetch('/sessions/{id}')`:
  - 200 → `setMessages(rehydrateMessages(body.messages))`
  - 404 → clear the stored id (empty state)
  - other/network error → empty state; composer stays usable
- Header action **New chat**: clear the stored id, reset the transport,
  `setMessages([])`.
