# Quickstart: Browser Resume

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
# frontend dev (optional): cd frontend && npm run dev
```

## Verify

1. Open `/`, send "I need a tent under $250"; wait for the reply.
2. Reload the page: the exchange reappears (fetched from `GET /sessions/{id}`).
3. Send another message: it continues the same session (the agent has context).
4. Click **New chat**: the transcript clears; the next message starts a new session.
5. In devtools, set `localStorage['commerce-agent.session'] = 'nope'` and reload:
   the app shows the empty state (the stale id is cleared), no error.

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/006-browser-resume/checkpoint.md` (SR-4/SR-5).
