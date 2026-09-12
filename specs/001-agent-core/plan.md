# Implementation Plan: Agent Core Loop

**Spec**: `specs/001-agent-core/spec.md`

## Approach

A single hand-written async loop. Dependencies point inward:

```
web/ (surface)  ->  app/core/loop.py  ->  app/ports  <-  app/adapters
                          |
                      app/tools (registry + catalog)
```

- `app/core/types.py` — provider-neutral message and streaming-event types.
- `app/core/events.py` — outward agent events and `to_wire`.
- `app/core/session.py` — the append-only log and `derive_messages` (SL-1).
- `app/core/loop.py` — the loop, the SL-1 guard, and tool dispatch.
- `app/ports/llm.py` — `LLMClient` service definition.
- `app/ports/event_sink.py` — `EventSink` service definition.
- `app/adapters/deepseek_client.py` — OpenAI-compatible streaming adapter.
- `app/adapters/mock_llm.py` — deterministic adapter for tests and keyless runs.
- `app/adapters/cli_sink.py` — CLI sink and a `ListSink` for tests.
- `app/tools/registry.py` — tool registry and guarded execution.
- `app/tools/catalog.py` — `search_products` over a tiny in-memory catalog.
- `web/main.py` — FastAPI app, SSE chat, health checks, static mount.

## Constitution check

- **SL-1**: messages built only via `derive_messages`; `build_request` re-derives
  and crashes on mismatch.
- **PB-2**: `LLMClient` and `EventSink` are seams (definition + provider + consumer).
- **PB-4**: the system prompt lives in `config/prompts/system.md`.
- **HR-2/HR-3**: context assembly, tool mediation, and state are harness jobs;
  tests are the sensor.
- **P6/CQ**: one responsibility per module; no premature abstraction.

## Testing

- Unit (`tests/unit/test_loop.py`): tool-then-reply, unknown tool, turn bound,
  deterministic projection.
- Integration (next): FastAPI app with a mock provider.
- E2E (next): a full conversation over SSE.

## Risks

- Provider streaming differences: mitigated by the narrow `LLMClient` port and the
  mock adapter.
- Context growth: addressed by feature 008 (context compaction).
