# Tasks: Knowledge Retrieval

**Feature**: `012-knowledge-retrieval` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Port + types + config

- [x] T001 Add `Chunk` to `app/core/types.py`
- [x] T002 `Retriever` protocol in `app/ports/retriever.py`
- [x] T003 `KnowledgeSettings` + env overrides in `app/core/settings.py` and `config/settings.yaml`

## Phase 2 — Provider + ingestion

- [x] T004 `app/adapters/retriever_memory.py` (`InMemoryRetriever`, TF-IDF)
- [x] T005 `app/knowledge/ingest.py` (`load_chunks`)
- [x] T006 `config/knowledge/{shipping,returns,warranty}.md`

## Phase 3 — Tool + wiring

- [x] T007 `app/tools/knowledge.py` (`search_knowledge`)
- [x] T008 `web/main.py`: `build_retriever`; register the tool

## Phase 4 — Tests + verify

- [x] T009 [P] Unit: `tests/unit/test_retriever.py` (ranking, idempotent add, empty)
- [x] T010 [P] Integration: `tests/integration/test_knowledge_tool.py`
- [x] T011 Add a `search_knowledge` eval scenario
- [x] T012 `scripts/ci.sh --fast`; browser checkpoint; docs; PR

## Dependencies

- T001/T002 before T004.
- T004/T005 before T007/T009.
- T012 last.
