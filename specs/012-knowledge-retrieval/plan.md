# Implementation Plan: Knowledge Retrieval

**Branch**: `012-knowledge-retrieval` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/012-knowledge-retrieval/spec.md`

## Summary

Add a `Retriever` port with a keyless in-memory TF-IDF provider over markdown
policy docs in `config/knowledge/` (paragraph chunks, idempotent ingestion), and a
`search_knowledge` tool returning grounded snippets with sources. No new
dependencies; no embeddings service.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib only (`math`, `re`, `pathlib`)

**Storage**: in-memory index built at startup from `config/knowledge/`

**Testing**: `pytest` (unit ranking; integration tool); an eval scenario

**Target Platform**: server

**Performance Goals**: tiny corpus; O(chunks × terms)

**Constraints**: keyless; idempotent; fail loud on bad config (PB-1)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P4 grounding | answers come from retrieved chunks with a source | PASS |
| PB-1 config as contract | `knowledge.provider` validated | PASS |
| PB-2 capability seam | Definition (Retriever) + Provider (memory) + Consumer (tool) | PASS |
| P5 / PB-5 | validate config; chunk ids stable | PASS |
| P6 / P8 | stdlib only; keyless | PASS |
| RD-2 | idempotent ingestion | PASS |

## Project Structure

```text
app/
├── core/types.py             # + Chunk
├── core/settings.py          # + KnowledgeSettings
├── ports/retriever.py        # NEW
├── adapters/retriever_memory.py  # NEW (TF-IDF)
├── knowledge/ingest.py       # NEW: load + chunk markdown
└── tools/knowledge.py        # NEW: search_knowledge
config/knowledge/*.md         # NEW: shipping, returns, warranty
web/main.py                   # build_retriever; register the tool
tests/unit/test_retriever.py
tests/integration/test_knowledge_tool.py
```

## Complexity Tracking

> No constitution violations; nothing to justify.
