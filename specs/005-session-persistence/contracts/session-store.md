# Contract: Session store

## Port (`app/ports/session_store.py`)

```python
class SessionRepository(Protocol):
    def create(self) -> Session: ...
    def get(self, session_id: str) -> Session | None: ...
    def get_or_create(self, session_id: str | None) -> Session: ...
    def save(self, session: Session) -> None: ...
```

Rules:
- `get_or_create(None)` creates a new session with a fresh unguessable id.
- `get_or_create(unknown_id)` creates a new session (the caller's id is not
  trusted as existing).
- `save` is idempotent: re-saving with no new events changes nothing.
- The port does not import the web layer or the model.

## Providers

| Provider | Module | Notes |
| --- | --- | --- |
| `memory` | `app/adapters/session_memory.py` | process lifetime; keyless |
| `sqlite` | `app/adapters/session_sqlite.py` | stdlib `sqlite3`; append-only events |

## Factory (`web/main.py`)

```python
def build_session_store(settings: Settings) -> SessionRepository: ...
```

## HTTP (web surface, WV-5)

`GET /sessions/{session_id}` → 200 with:

```json
{
  "session_id": "…",
  "messages": [
    {"role": "user", "content": "I need a tent"},
    {"role": "assistant", "content": "…", "tool_calls": [{"id": "…", "name": "search_products"}]},
    {"role": "tool", "content": "…", "tool_call_id": "…", "name": "search_products"}
  ]
}
```

Unknown id → 404.

## Consumer (web `/chat`)

- Resolve the session via `get_or_create(request.session_id)`.
- Stream the turn as today.
- In the stream's `finally`, `store.save(session)`.
