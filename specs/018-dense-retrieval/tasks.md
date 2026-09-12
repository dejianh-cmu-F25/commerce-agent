# Tasks: Dense Retrieval

**Feature**: `018-dense-retrieval` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 1 — Ports + config

- [x] T001 `app/ports/embedding.py`, `app/ports/vector_store.py`
- [x] T002 `app/core/settings.py`: embedding/vector_store/knowledge literals + keyless defaults; `VECTOR_STORE_PROVIDER` env
- [x] T003 `config/settings.yaml` + `.env.example` (parity)

## Phase 2 — Providers + retriever

- [x] T004 `app/adapters/embedding_hash.py` (keyless)
- [x] T005 `app/adapters/embedding_openai.py` (optional)
- [x] T006 `app/adapters/vector_memory.py` (cosine, idempotent)
- [x] T007 `app/adapters/retriever_dense.py`

## Phase 3 — Wiring

- [x] T008 `web/main.py`: `build_embedding`, `build_vector_store`, branch `build_retriever`

## Phase 4 — Tests + verify

- [x] T009 [P] Unit: hashing, store, dense retriever
- [x] T010 [P] Integration: dense over `config/knowledge/`
- [x] T011 `docs/architecture.md`; Agent Note
- [x] T012 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001/T002 before T004–T008.
- T004/T006/T007 before T009/T010.
- T012 last.
