# Quickstart: Session Persistence

## Configure

`config/settings.yaml`:

```yaml
session:
  store: sqlite          # memory | sqlite
  sqlite_path: ./data/db/sessions.sqlite
```

Env overrides: `SESSION_STORE`, `SESSION_SQLITE_PATH`.

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify (API)

```sh
# 1. send a message; capture the session id from the SSE stream
curl -N -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"I need a tent under $250"}' | head

# 2. fetch the session (use the id from SessionStarted)
curl -s localhost:8000/sessions/<id> | jq .

# 3. restart the server, then fetch the same id again — the messages persist
```

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

The chat is user-visible; a checkpoint is recorded at
`specs/005-session-persistence/checkpoint.md` (SR-4/SR-5).
