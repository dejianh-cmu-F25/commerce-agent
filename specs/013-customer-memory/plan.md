# Implementation Plan: Customer Memory

**Branch**: `013-customer-memory` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/013-customer-memory/spec.md`

## Summary

Add a `MemoryStore` port with a keyless in-memory provider and a durable SQLite
provider, a deterministic keyless extractor over the customer's own text, and a
`memory` note event in the session log so recalled facts are injected into the
model context through the single `derive_messages` path (SL-1). Sessions carry a
client-supplied `customer_id`. The web surface gains a Memory tab (list + forget)
and `/memory` endpoints; the loop gains a `memory` span. No new dependencies.

## Technical Context

**Language/Version**: Python 3.13; React 19 + TypeScript (frontend)

**Primary Dependencies**: Python stdlib only (`re`, `sqlite3`, `pathlib`);
frontend uses the existing Vite/React/shadcn stack

**Storage**: SQLite `data/db/memory.sqlite` (durable) or in-memory; facts keyed
idempotently by `(customer_id, kind, value)`

**Testing**: `pytest` (unit: extractor, stores, SL-1 injection; integration:
`/memory` API + cross-session recall); one eval scenario

**Target Platform**: server + browser

**Performance Goals**: tiny per-customer fact set; O(facts) recall

**Constraints**: keyless; deterministic; fail loud on bad config (PB-1); memory
failure degrades to no-memory (RD-1); recalled facts are logged (SL-1)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes | memory is read-only context; extraction is harness-driven, not model-driven | PASS |
| P4 grounding | facts come only from the customer's text; never prices/stock/policy | PASS |
| P5 / PB-2 capability seam | Definition (`MemoryStore`) + Providers (memory, sqlite) + Consumer (loop/web) | PASS |
| PB-1 config as contract | `memory.provider` validated; unknown provider fails loud | PASS |
| PB-4 prompts external | no new model step; no inline prompt | PASS |
| SL-1 model-visible means logged | recalled facts appended as a `MemoryNote` event; `derive_messages` folds them in; guard unchanged | PASS |
| SL-2 / OB-1 | `memory` span under the turn `trace_id` | PASS |
| P6 / P8 | stdlib only; keyless; deterministic | PASS |
| RD-1 resilience | store errors degrade to no-memory; extraction has no model dependency | PASS |
| RD-2 idempotent data | unique key per `(customer, kind, value)`; forget is traceable | PASS |
| WV-5 web entry | Memory tab + `/memory` endpoints | PASS |
| HR-11 extension point | loop change documented in `docs/architecture.md` | PASS |

## Project Structure

```text
app/
├── core/types.py             # + MemoryFact
├── core/session.py           # + MemoryNote event, customer_id; derive_messages folds memory
├── core/loop.py              # recall + inject + extract; memory span
├── core/settings.py          # + MemorySettings (provider, sqlite_path, extraction)
├── ports/memory.py           # NEW: MemoryStore
├── adapters/memory_memory.py # NEW: InMemoryMemoryStore
├── adapters/memory_sqlite.py # NEW: SqliteMemoryStore
├── memory/extract.py         # NEW: deterministic extractor
├── adapters/session_memory.py / session_sqlite.py  # persist customer_id + MemoryNote
web/main.py                   # customer_id on /chat; /memory endpoints; build_memory
config/settings.yaml          # memory.provider/path
frontend/src/
├── lib/memory.ts             # NEW: API client
├── lib/transport.ts          # customer id + send it on /chat
├── components/app/memory-view.tsx  # NEW
└── App.tsx                   # Memory tab
tests/unit/test_memory_extract.py, test_memory_store.py, test_memory_injection.py
tests/integration/test_memory_api.py
evals/scenarios.py            # + memory_recall scenario
docs/architecture.md          # loop/extension-point update
docs/notes/implemented/architecture/...-customer-memory.md
```

## Design decisions

- **Recalled facts are logged.** Recall appends a `MemoryNote(facts)` session
  event at most once per session; `derive_messages` folds `MemoryNote` into the
  system message. This keeps SL-1 true: the model context is a pure function of
  the log. A session with no facts gets no `MemoryNote`, so the context is
  identical to the no-memory baseline.
- **Extraction is deterministic and keyless.** A bounded pattern set over the
  customer's text only. No model call, so no budget and no nondeterminism. The
  deferred LLM extractor must fall back to this one (RD-1).
- **Identity is opaque.** `customer_id` is generated in the browser and sent on
  `/chat`; it is not authentication. Sessions without it run memory-disabled.
- **Forget is first-class.** A per-fact and a forget-all endpoint back the Memory
  view; forgetting removes the fact from future recall.

## Complexity Tracking

> One loop change: `Agent` accepts an optional `MemoryStore` and emits a `memory`
> span. This is the documented extension point for the "memory" harness job
> (HR-2, HR-11); `docs/architecture.md` is updated in the same PR. No new
> dependency and no new model call.
