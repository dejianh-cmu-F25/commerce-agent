# Implementation Plan: Chroma Vector Store

**Branch**: `021-chroma-vector-store` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `chromadb` as a base dependency and `app/adapters/vector_chroma.py`
(`ChromaVectorStore`) behind the existing `VectorStore` port; wire
`build_vector_store`; make the shipped config default to dense + Chroma. Keep the
in-memory store for tests and the keyless path.

## Technical Context

**Language/Version**: Python 3.13 (dev) / 3.12 (image)

**Primary Dependencies**: `chromadb>=1.5,<2` (base)

**Storage**: `vector_store.persist_directory` (`./data/chroma`; a docker volume)

**Testing**: `pytest` (integration: parity with `InMemoryVectorStore`,
idempotency, persistence, fail-loud)

**Constraints**: keyless default embedding; no model download; telemetry off;
config-selected (PB-1); idempotent (RD-2)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| PB-1 config as contract | `vector_store.provider` selects the store; missing dep fails loud | PASS |
| PB-2 capability seam | one more provider behind `VectorStore` | PASS |
| P6 simplicity | embedded persistent client; no server | PASS |
| P8 reproducible | keyless `hash` embedding; no key; no model download | PASS |
| RD-2 idempotent | upsert keyed by chunk id | PASS |
| DP-6 volumes | data under `./data/chroma` (mounted) | PASS |
| HR-11 | documented seam | PASS |

## Project Structure

```text
app/adapters/vector_chroma.py   # NEW
web/main.py                     # build_vector_store: chroma
pyproject.toml; uv.lock         # + chromadb
config/settings.yaml            # dense + chroma defaults
.env.example                    # VECTOR_STORE_PROVIDER / KNOWLEDGE_PROVIDER
tests/integration/test_chroma_store.py
tests/integration/test_knowledge_dense.py   # update the fail-loud assertion
docs/architecture.md; Agent Note
```

## Design decisions

- **Embedded `PersistentClient`.** No separate service; matches DP-1/DP-6.
- **Vectors supplied by the harness.** Disable Chroma's default embedding function
  so nothing downloads; `hash` keeps it keyless.
- **Telemetry off.** `anonymized_telemetry=False` for privacy/keyless.
- **Cosine space, `score = 1 - distance`.** Matches the port's "positive score,
  best first" contract and the in-memory store.
- **App default = dense + Chroma; code default = memory.** Tests construct
  `Settings()` (memory) to stay fast and keyless; the shipped `settings.yaml`
  selects Chroma.

## Complexity Tracking

> One heavy dependency, accepted by the maintainer. No other violations.
