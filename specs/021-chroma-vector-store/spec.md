# Feature Specification: Chroma Vector Store

**Feature Branch**: `021-chroma-vector-store`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a Chroma-backed `VectorStore` provider (persistent, cosine) behind
the existing port. The app's shipped configuration uses dense retrieval with
Chroma; the in-memory store remains the keyless/test fallback.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dense retrieval backed by Chroma (Priority: P1)

With `knowledge.provider: dense` and `vector_store.provider: chroma`, policy
questions are answered from the nearest chunks stored in a persistent Chroma
collection, with the same sources and ranking semantics as the in-memory store.

**Why this priority**: The project wants a real vector database; Chroma is the
chosen one, behind the existing `VectorStore` port (PB-2).

**Independent Test**: Store the same chunks/vectors in both stores and assert the
top hits match; query a Chroma collection built from `config/knowledge/`.

**Acceptance Scenarios**:

1. **Given** chunks and vectors, **When** they are upserted into Chroma and
   queried, **Then** the nearest chunk matches the in-memory store's result.
2. **Given** the app config, **When** it starts, **Then** dense retrieval uses the
   Chroma store at `vector_store.persist_directory`.

---

### User Story 2 - Idempotent and persistent (Priority: P1)

Re-ingesting does not duplicate vectors, and data survives a restart.

**Independent Test**: Upsert twice and assert the count is unchanged; build a
second client on the same directory and assert the count persists.

**Acceptance Scenarios**:

1. **Given** ingested chunks, **When** they are added again, **Then** the count is
   unchanged (RD-2).
2. **Given** a persisted directory, **When** a new client opens it, **Then** the
   vectors are still present (DP-6).

---

### User Story 3 - Config-selected, fail-loud, keyless (Priority: P2)

The provider is selected by configuration; if the dependency is missing it fails
loud; the keyless embedding still works.

**Independent Test**: Select `chroma` and assert a store is built; assert the
default embedding (all-MiniLM) is never triggered and telemetry is off.

**Acceptance Scenarios**:

1. **Given** `vector_store.provider: chroma`, **When** the app starts, **Then** a
   Chroma store is built (no model download, no telemetry).
2. **Given** a missing `chromadb`, **When** `chroma` is selected, **Then** it
   fails loud with a clear message (PB-1).

---

### Edge Cases

- **Missing directory**: created on first use.
- **Empty collection**: `query` returns nothing.
- **Unrelated query**: scores ≤ 0 are filtered out (the port contract).
- **Concurrent access**: one client/collection per process.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `ChromaVectorStore` implementing the
  `VectorStore` port (upsert, cosine query, size).
- **FR-002**: The collection MUST use cosine space; a query's distance MUST be
  converted to `score = 1 - distance`, and non-positive scores filtered.
- **FR-003**: Upsert MUST be keyed by chunk id and idempotent (RD-2); chunk
  `source` MUST be preserved as metadata.
- **FR-004**: The store MUST persist to `vector_store.persist_directory` and
  survive a new client (DP-6).
- **FR-005**: Chroma's default embedding function MUST NOT be used (the harness
  supplies vectors), and anonymized telemetry MUST be disabled.
- **FR-006**: `vector_store.provider` MUST select `memory` or `chroma`; a missing
  `chromadb` MUST fail loud (PB-1).
- **FR-007**: The shipped configuration MUST default to `knowledge.provider:
  dense` and `vector_store.provider: chroma`; the in-memory store remains for
  tests and keyless runs.

### Key Entities

- **ChromaVectorStore**: the `VectorStore` provider over a persistent Chroma
  collection.

## Observability

- Ingestion and retrieval are invoked by `DenseRetriever` through the existing
  `search_knowledge` tool, whose call is already traced (OB-1). No new span.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chroma and in-memory stores return the same top hit for the same
  chunks/vectors (parity).
- **SC-002**: Re-ingesting does not change the vector count; a new client on the
  same directory sees the same count.
- **SC-003**: No model download and no telemetry on first use.
- **SC-004**: The keyless default (`memory`) is unchanged.
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes.

## Assumptions

- Embedded `PersistentClient` (no separate Chroma server) matches the project's
  file-based, single-command design (DP-1, DP-6).
- Chroma stores whatever the configured `EmbeddingProvider` produces; the keyless
  `hash` embedding keeps the default path keyless.
- The corpus is tiny; HNSW defaults are fine.

## Measured Results

- Chroma↔memory parity: identical top hit and hit set on the same vectors;
  idempotent upsert (count unchanged) and persistence across a new client.
- Dense + Chroma retrieval: hit-rate@3 **1.000**, hard hit@3 **1.000**.
- Source: `tests/integration/test_chroma_store.py`, `evals/bench.py`; aggregate:
  [`specs/RESULTS.md`](../RESULTS.md).
