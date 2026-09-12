# Tasks: Customer Memory

**Feature**: `013-customer-memory` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Port, types, config

- [x] T001 Add `MemoryFact` to `app/core/types.py`
- [x] T002 `MemoryStore` protocol in `app/ports/memory.py`
- [x] T003 `MemorySettings` (provider, sqlite_path, extraction) + env overrides in `app/core/settings.py` and `config/settings.yaml`

## Phase 2 — Providers + extractor

- [x] T004 `app/adapters/memory_memory.py` (`InMemoryMemoryStore`)
- [x] T005 `app/adapters/memory_sqlite.py` (`SqliteMemoryStore`, idempotent)
- [x] T006 `app/memory/extract.py` (`extract_facts`, deterministic)

## Phase 3 — Session log + loop (SL-1)

- [x] T007 `MemoryNote` event + `Session.customer_id`; fold memory in `derive_messages`
- [x] T008 Persist `customer_id` and `MemoryNote` in the session stores
- [x] T009 `Agent`: optional `MemoryStore`; recall+inject once per session; extract after the turn; `memory` span

## Phase 4 — Web + frontend

- [x] T010 `web/main.py`: `build_memory`; `customer_id` on `/chat`; `/memory` list/forget endpoints
- [x] T011 Frontend: customer id in `transport.ts`; `lib/memory.ts`; `MemoryView`; Memory tab in `App.tsx`

## Phase 5 — Tests + verify

- [x] T012 [P] Unit: `tests/unit/test_memory_extract.py`
- [x] T013 [P] Unit: `tests/unit/test_memory_store.py`
- [x] T014 [P] Unit: `tests/unit/test_memory_injection.py` (SL-1 fold, no-fact baseline)
- [x] T015 [P] Integration: `tests/integration/test_memory_api.py` (cross-session recall, forget)
- [x] T016 Add a `memory_recall` eval scenario
- [x] T017 Update `docs/architecture.md`; add the Agent Note
- [x] T018 `scripts/ci.sh --fast`; browser checkpoint; review; PR

## Dependencies

- T001/T002 before T004/T005.
- T006 before T009.
- T007/T008 before T009/T015.
- T010 before T011/T015.
- T018 last.
