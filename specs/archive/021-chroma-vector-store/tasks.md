# Tasks: Chroma Vector Store

**Feature**: `021-chroma-vector-store` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 Add `chromadb>=1.5,<2` to `pyproject.toml`; lock
- [x] T002 `app/adapters/vector_chroma.py` (`ChromaVectorStore`)
- [x] T003 `web/main.py`: `build_vector_store` builds Chroma
- [x] T004 `config/settings.yaml` dense + chroma; `.env.example` values (parity)
- [x] T005 [P] `tests/integration/test_chroma_store.py` (parity, idempotency, persistence, fail-loud)
- [x] T006 Update `tests/integration/test_knowledge_dense.py` fail-loud assertion
- [x] T007 `docs/architecture.md`; Agent Note
- [x] T008 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001 before T002/T005.
- T002/T003 before T005/T006.
- T008 last.
