# Architecture

## Agent = Model + Harness

The model (DeepSeek, provider-neutral) decides. Everything else is the
**harness**: the software that turns a decision into an effect and makes it
trustworthy.

The harness boundary is explicit. It **begins** where identity, state, policy,
budgets, and model invocation are coordinated, and **ends** at the adapters to
providers, tools, storage, approval, and telemetry.

## Layers

Dependencies point inward only.

| Layer | Contents | Depends on |
| --- | --- | --- |
| L4 Surfaces | `web/` (chat, SSE), CLI | L3 |
| L3 Capabilities | `app/tools`, `app/skills`, `app/memory`, `app/gates` | L2 |
| L2 Adapters | `app/adapters` (DeepSeek, mock, SQLite, Chroma, SSE, CLI) | L1 |
| L1 Ports | `app/ports` (LLM, Backend, Retriever, Memory, Tracer, EventSink) | L0 |
| L0 Core | `app/core` (loop, session, events, settings, prompts) | none |

`app/core` imports only `app/ports`. Adapters implement the ports and are
injected. This is the dependency-inversion rule (PB-2, PB-3).

## The harness's jobs

1. **Context assembly** — build model messages from the session log (SL-1).
2. **Tool mediation** — registry, schemas, guarded execution.
3. **State persistence** — the session log; cart and provenance as derived state.
4. **Control** — gates: provenance, caps, approval.
5. **Memory** — cross-session facts.
6. **Observability** — `trace_id` spans and metrics.
7. **Recovery** — reload and resume a session.
8. **Delivery** — Docker and CI.

## Data flow

**Turn flow**

```
Browser --POST /chat--> Web --EventSink--> Agent loop
  loop: build messages from session log  (SL-1 guard)
        --> LLMClient.stream --> text deltas / tool calls
        --> gates --> tools --> adapters (backend, retriever)
        --> append to session log
  loop --AgentEvent--> Web --SSE--> Browser
  every step --> trace span --> logs/traces.jsonl
```

**Ingestion flow** (feature 008)

```
Docs -> Loader -> Chunker -> Transform -> Embed -> Upsert
     -> Chroma (dense) + BM25 (sparse)   [idempotency key = doc hash]
```

**Observability flow**

```
span(trace_id, inputs, outputs, duration, tokens)
  -> logs/traces.jsonl -> Trace Viewer (web)
  -> metrics (latency, tokens, cost, cache hit, tool success)
```

**Control flow**

```
Guides (feedforward): system prompt, skills, tool contracts, layering rules
Sensors (feedback):   ruff, pyright, tests, evals, gates
                       -> block the PR or trigger a fix
```

## Where new behavior goes (HR-11)

| Goal | Mechanism |
| --- | --- |
| Add a model provider | Implement `app/ports/llm.LLMClient`; select it in `settings.yaml` |
| Add a model-facing capability | Register a `ToolSpec` + handler in `app/tools/registry.py` |
| Add a long-tail procedure | Add `skills/<name>/SKILL.md` |
| Add a storefront/merchant system | Implement `StorefrontBackend` / `MerchantBackend` |
| Add retrieval | Implement `Retriever`; wire `dense`/`sparse`/`fusion` |
| Change chunking | Implement `ChunkingStrategy`; select it in config |
| Add a write guardrail | Add a link to the gate pipeline in `app/gates/` |
| Add a UI component | Register `component_type -> renderer` in `web/static/app.js` |
| Add a surface (CLI, websocket) | Implement `EventSink`; mount it |
| Add durable session state | Extend `SessionEvent`; render and replay from the log |
| Add background work | Add a job runner behind a port |
| Add deployment target | Extend `docker-compose.yml`; keep config in env |

Changing the loop itself is the exception, not the rule. If you change
`app/core/loop.py`, update this document in the same pull request.
