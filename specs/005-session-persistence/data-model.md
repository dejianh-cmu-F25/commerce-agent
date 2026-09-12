# Data Model: Session Persistence

## Domain (unchanged)

`Session` (`app/core/session.py`): `id`, `events: list[SessionEvent]`,
`cart: list[CartLine]`, `provenance: set[str]`.

`SessionEvent` = `UserMessage | AssistantMessage | ToolResultEvent`.

## SQLite schema (`session_sqlite`)

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session_events (
    session_id TEXT NOT NULL,
    seq        INTEGER NOT NULL,          -- index in the log; stable order
    kind       TEXT NOT NULL,             -- user | assistant | tool_result
    payload    TEXT NOT NULL,             -- JSON
    PRIMARY KEY (session_id, seq)
);

CREATE TABLE IF NOT EXISTS session_provenance (
    session_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    PRIMARY KEY (session_id, product_id)
);

CREATE TABLE IF NOT EXISTS session_cart (
    session_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    title      TEXT NOT NULL,
    quantity   INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    PRIMARY KEY (session_id, product_id)
);
```

## Event serialization

| kind | payload |
| --- | --- |
| `user` | `{text}` |
| `assistant` | `{text, tool_calls: [{id, name, arguments}]}` |
| `tool_result` | `{call_id, name, content, status}` |

Loading maps each row back to the matching `SessionEvent`; an unknown `kind` raises
(no silent drop).

## Config (`SessionSettings`)

| Field | Type | Default |
| --- | --- | --- |
| `store` | `"memory" \| "sqlite"` | `"sqlite"` |
| `sqlite_path` | `str` | `"./data/db/sessions.sqlite"` |

Env overrides: `SESSION_STORE`, `SESSION_SQLITE_PATH`.

## Round-trip invariant

`derive_messages(load(save(session)), prompt) == derive_messages(session, prompt)`.
