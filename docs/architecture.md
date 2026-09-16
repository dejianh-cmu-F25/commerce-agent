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
| L4 Surfaces | `frontend/` (React SPA + AI Elements), `web/` (SSE API), CLI | L3 |
| L3 Capabilities | `app/tools`, `app/skills`, `app/memory`, `app/gates` | L2 |
| L2 Adapters | `app/adapters` (DeepSeek, mock, SQLite, SSE, CLI, storefront, session, tracer, merchant, memory, embedding, vector) | L1 |
| L1 Ports | `app/ports` (LLM, Storefront, Merchant, Session, Tracer, Backend, Retriever, Embedding, VectorStore, Memory, EventSink, PostPurchase, Catalog[planned]) | L0 |
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
  loop: recall customer memory (MemoryStore) --> append MemoryNote to the log
        build messages from session log  (SL-1 guard)
        --> LLMClient.stream --> text deltas / tool calls
        --> gates --> tools --> adapters (backend, retriever)
        --> append to session log
        extract customer facts from the user's text (deterministic)
  loop --AgentEvent--> Web --SSE--> Browser
  every step --> trace span (turn/llm/tool/memory) --> logs/traces.jsonl
```

**Ingestion flow** (feature 008)

```
Docs -> Loader -> Chunker -> Transform -> Embed -> Upsert
     -> Chroma (dense) + BM25 (sparse)   [idempotency key = doc hash]
```

**Observability flow**

```
span(trace_id, inputs, outputs, duration, tokens)   # llm span records cache hit/miss tokens
  -> logs/traces.jsonl -> Trace Viewer (web)
  -> Metrics view (latency by span, tokens, cost, cache hit, tool success/failure)
     via GET /metrics -> app/core/metrics.summarize(recent_spans)
```

**Control flow**

```
Guides (feedforward): system prompt, skills, tool contracts, layering rules
Sensors (feedback):   ruff, pyright, tests, evals, gates
                       -> block the PR or trigger a fix
```

**Gates (control, 046 hardening).** A gate is decision-only (`GateResult`), never
an effect (P3). Gates run at the single execution point, `ToolRegistry.execute`, so
no surface can forget one. A gate declares `applies_to` (tool names and/or an
effect class) and `priority`; `app/gates/registry.py:order_gates` resolves the
order explicitly (an unknown name fails loud, PB-1/PB-3) and `GateSet.select` picks
the gates for a call. A `proposal` / `irreversible` tool with no covering gate is
refused (fail-closed). Adding a gate is one class plus one line in
`app/gates/factory.py:build_gate_set` -- no tool changes. HITL is `ApprovalGate`;
`config/settings.yaml:gates` can disable gates by name or pin their order.

## Where new behavior goes (HR-11)

| Goal | Mechanism |
| --- | --- |
| Add a model provider | Implement `app/ports/llm.LLMClient`; select it in `settings.yaml` |
| Add a model-facing capability | Register a `ToolSpec` + handler in `app/tools/registry.py` |
| Add a long-tail procedure | Add `skills/<name>/SKILL.md`; `app/skills/loader.py` advertises it in the system prompt and `use_skill` loads the body on demand |
| Add a storefront/merchant system | Implement `StorefrontBackend` (`app/ports/storefront.py`) / `MerchantBackend`; select the provider in `settings.yaml` |
| Add a commerce backend | Implement `PostPurchaseBackend` (`app/ports/post_purchase.py`); `post_purchase.provider` selects `shopify` (real, read-only) or `memory` |
| Add a product catalog | Implement the `Catalog` port (planned, feature 045); the ESCI adapter ranks a real catalog against human relevance labels |
| Add post-purchase orders | Extend `StorefrontBackend` (orders) and register tools in `app/tools/orders.py`; demo orders live in `app/adapters/order_seed.py` |
| Change the return policy | Edit `config/policies/amazon.yaml` (feature 046); the prose and the engine derive from it |
| Add retrieval | Implement `Retriever` (`app/ports/retriever.py`); `knowledge.provider` selects `memory` (keyless TF-IDF, default) or `dense` |
| Add embeddings | Implement `EmbeddingProvider` (`app/ports/embedding.py`); `embedding.provider` selects keyless `hash` (default) or `openai` |
| Add a vector store | Implement `VectorStore` (`app/ports/vector_store.py`); `vector_store.provider` selects persistent `chroma` (default) or in-process `memory` |
| Add a passage index / metadata filter | Build chunks with `catalog_index.catalog_chunks` and aggregate with `PassageCatalogIndex`; a `where` clause filters on `Chunk.metadata` (`app/core/filters.py`), the same shape across the retrievers and Chroma (feature 047) |
| Add a query-understanding step | Implement `QueryUnderstanding` (`app/ports/query_understanding.py`); `catalog.query_understanding` selects `none` (default), `rules` (keyless, `app/adapters/query_rules.py`) or `llm` (HyDE-style, `app/adapters/query_llm.py`; prompt in `config/prompts/query_rewrite.md`) |
| Add customer memory | Implement `MemoryStore` (`app/ports/memory.py`); select it in `settings.yaml` (keyless memory + SQLite providers) |
| Change memory extraction | Edit `app/memory/extract.py`; the deterministic extractor is the fallback for any future LLM extractor (RD-1) |
| Run or change the gold scenarios | `evals/runner.py` + `evals/scenarios.py` are the source of truth: 13 keyless scenarios driving the **shipped** closed-loop tools (`get_order_status`, `list_returnable_items`, `propose_return_decision`) over `evals/order_fixtures.py`; `evals/run.py` runs them in the gate. The 016 spec is archived, so the code and this row are the documentation |
| Change chunking | Edit `app/knowledge/ingest.py` (one chunk per section, heading kept) and `ingestion.chunk_size` |
| Add a write guardrail | Add a `Gate` in `app/gates/` (name + `applies_to` + `priority` + `check`) and register it in `app/gates/factory.py`; the registry runs it at `ToolRegistry.execute` |
| Add or change a UI component | Add an AI Elements/shadcn component under `frontend/src/components`; wire it in `frontend/src/App.tsx` |
| Change how backend events reach the UI | Edit `frontend/src/lib/transport.ts` (SSE → AI SDK `UIMessageChunk`) |
| Add a UI state or a11y behavior | Follow `docs/ui-conventions.md`; update the spec's `## UI Requirements` |
| Add a surface (CLI, websocket) | Implement `EventSink`; mount it |
| Add an evaluation view | `frontend/src/components/app/report-view.tsx` renders `evals/report.md` (served by `GET /report`) through the sanitizing markdown renderer |
| Add durable session state | Extend `SessionEvent`; render and replay from the log |
| Add a session store | Implement `SessionRepository` (`app/ports/session_store.py`); select it in `settings.yaml` |
| Add a tracer / span | Emit a `Span` via the `Tracer` port; add attributes (redacted) in the loop |
| Add a metric | Add attributes to the relevant span, then aggregate in `app/core/metrics.py` and surface in the Metrics view |
| Add an eval scenario | Add a `Scenario` in `evals/scenarios.py` (scripted turns + expected outcomes); the gate CLI and the web Scenario Runner both pick it up via `evals/runner.py` |
| Add a retrieval query | Add a `RetrievalCase` in `evals/retrieval_set.py`; the keyless benchmark and `evals/report.md` pick it up |
| Run the gold scenarios from the web | The Scenario Runner calls `evals.runner.run_scenarios` (same code as the gate); served by `GET /scenarios` + `POST /scenarios/run` (WV-4) |
| Add background work | Add a job runner behind a port |
| Add deployment target | Extend `docker-compose.yml`; keep config in env |

Changing the loop itself is the exception, not the rule. If you change
`app/core/loop.py`, update this document in the same pull request. The loop
closes each provider stream deterministically after the final event, so stopping
on `Finish` never leaves an async generator to be collected mid-flight.

## Runtime wiring: the journey agent (feature 046)

`web/main.py:build_agent` wires the closed-loop tool set:

- **storefront**: `search_products` (catalog), `cart_*` (cart), `search_knowledge`
  (policy retrieval from the SoT-derived corpus).
- **cart backend** (`app/ports/cart.py`, resolved by `web/main.py:build_cart`): `session`
  (keyless default — lines live on the session) or `shopify_storefront`
  (`app/adapters/cart_shopify.py`, a real Storefront cart; needs
  `SHOPIFY_STOREFRONT_TOKEN`, a credential this project's store does not have, so that
  path is implemented and MockTransport-tested but **not live-verified**). Either
  provider mirrors its lines onto the session, so the transcript and session
  persistence are unchanged.
- **checkout**: `create/update/complete_checkout` over the simulated ACP adapter
  (`complete_checkout` is HITL-gated).
- **customer-accounts**: `get_order_status`, `list_returnable_items`,
  `propose_return_decision`, validated at runtime by `PolicyGate`
  (`app/gates/policy.py`) against the policy SoT (`config/policies/amazon.yaml`).

The system prompt is `config/prompts/journey.md` and holds **only the procedure**,
never policy facts. **Legacy path**: `app/tools/orders.py` and
`app/returns/policy.py` are deprecated (kept for the legacy storefront evals) and
are no longer wired into the app.
