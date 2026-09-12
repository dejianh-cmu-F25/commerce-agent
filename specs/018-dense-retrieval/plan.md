# Implementation Plan: Dense Retrieval

**Branch**: `018-dense-retrieval` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `Embedding` and `VectorStore` ports, keyless `hash` + optional `openai`
embedding providers, an in-process cosine `VectorStore`, and a `DenseRetriever`
behind the existing `Retriever` port. `knowledge.provider: memory|dense` selects
the path; the keyless TF-IDF default is unchanged. No heavy dependency.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib (`hashlib`, `math`, `re`) for hashing; the
existing `openai` package for the optional provider

**Storage**: in-process vectors

**Testing**: `pytest` (unit: hashing determinism, store ranking, dense retriever;
integration: dense over `config/knowledge/`)

**Constraints**: keyless default (P8); config-selected, fail loud (PB-1);
idempotent ingestion (RD-2)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P4 grounding | chunks with sources, unchanged tool contract | PASS |
| PB-1 config as contract | `knowledge.provider`, `embedding.provider` validated; unknown fails loud | PASS |
| PB-2 capability seam | Embedding + VectorStore definitions with providers | PASS |
| P6 / P8 | stdlib hashing; no heavy dep; keyless default | PASS |
| RD-2 | upsert keyed by chunk id; re-add is a no-op | PASS |
| RD-1 | provider errors surface as tool errors | PASS |
| HR-11 | new behavior attaches to the Retriever seam; documented | PASS |

## Project Structure

```text
app/
├── ports/embedding.py        # NEW
├── ports/vector_store.py     # NEW
├── adapters/embedding_hash.py    # NEW (keyless)
├── adapters/embedding_openai.py  # NEW (optional)
├── adapters/vector_memory.py     # NEW (cosine)
├── adapters/retriever_dense.py   # NEW
├── core/settings.py          # embedding/vector_store/knowledge literals + defaults
web/main.py                   # build_embedding/build_vector_store; branch in build_retriever
config/settings.yaml; .env.example
tests/unit/test_embedding_hash.py, test_vector_store.py, test_retriever_dense.py
tests/integration/test_knowledge_dense.py
docs/architecture.md; Agent Note
```

## Design decisions

- **Keyless dense default.** Feature hashing (`hashlib`) gives deterministic,
  dependency-free vectors; `openai` is opt-in for semantics. This keeps P8.
- **Store keyed by chunk id.** Idempotent ingestion falls out of upsert semantics.
- **Chroma deferred.** Its ~31-dep tree is too heavy for this project; the
  `VectorStore` port is the documented seam for it later.
- **Default literals changed to the keyless option** (`embedding.provider: hash`,
  `vector_store.provider: memory`), matching what is implemented.

## Complexity Tracking

> No violations. One new pair of ports with keyless providers; no heavy dep.
