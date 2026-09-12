# Quickstart: Observability

## Configure

`config/settings.yaml`:

```yaml
observability:
  trace_enabled: true
  trace_file: ./logs/traces.jsonl
  trace_max_attr_len: 500
```

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify

```sh
# send a message, then:
curl -s localhost:8000/traces | jq .
curl -s localhost:8000/traces/<trace_id> | jq '.spans[].name'
# expect: turn, llm, tool

tail -n 3 logs/traces.jsonl | jq -c '{name, duration: (.end_ms - .start_ms), status}'
```

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/007-observability/checkpoint.md` (SR-4/SR-5).
