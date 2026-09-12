# Quickstart: Knowledge Retrieval

## Configure

`config/settings.yaml`:

```yaml
knowledge:
  provider: memory
  path: ./config/knowledge
  top_k: 3
  min_chars: 40
```

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify

Open `/` and ask "what is your return policy?". The `search_knowledge` step runs
and the answer cites `returns.md`. Ask an unrelated question: the agent says it
does not know.

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/012-knowledge-retrieval/checkpoint.md` (SR-4/SR-5).
