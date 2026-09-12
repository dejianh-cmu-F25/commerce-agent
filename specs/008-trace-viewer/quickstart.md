# Quickstart: Web Trace Viewer

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify

1. Open `/`, send a message (this writes a trace).
2. Click **Traces** in the header: the turn's trace is listed with its duration
   and span count.
3. Click the trace: the timeline shows `turn` with `llm`/`tool` children, their
   durations, statuses, and attributes (tokens, cost, tool name).
4. Click **Refresh**: the list reloads. Click **Chat**: the transcript is intact.

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/008-trace-viewer/checkpoint.md` (SR-4/SR-5).
