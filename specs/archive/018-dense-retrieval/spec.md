# Feature Specification: Dense Retrieval

**Feature Branch**: `018-dense-retrieval`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a dense retrieval path behind the existing `Retriever` port: an
`Embedding` port (keyless hashing default; OpenAI optional) and a `VectorStore`
port (in-process cosine), selected by configuration while the keyless TF-IDF
retriever stays the default (P8).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dense policy answers, keylessly (Priority: P1)

With `knowledge.provider: dense`, the agent answers policy questions from the
nearest policy chunks by vector similarity, still with sources and no provider
key.

**Why this priority**: The README promises retrieval; TF-IDF is lexical only. A
dense path is the semantic upgrade, and it must stay reproducible.

**Independent Test**: Build the dense retriever over `config/knowledge/`, retrieve
for a returns query, and assert the top chunk comes from `returns.md`.

**Acceptance Scenarios**:

1. **Given** dense retrieval configured with the keyless embedding, **When** a
   returns query runs, **Then** the top chunk is from `returns.md`.
2. **Given** the keyless default (`knowledge.provider: memory`), **When** the app
   starts, **Then** behavior is unchanged (TF-IDF).

---

### User Story 2 - Pluggable embeddings and store (Priority: P1)

Embeddings and the vector store are contracts with providers, selected by config;
an unknown provider fails loud.

**Independent Test**: Build each provider; assert the keyless one is
deterministic and an unknown provider is rejected.

**Acceptance Scenarios**:

1. **Given** `embedding.provider: hash`, **When** the same text is embedded
   twice, **Then** the vectors are identical.
2. **Given** an unknown provider, **When** settings load, **Then** it fails loud.

---

### User Story 3 - Idempotent ingestion (Priority: P2)

Re-adding chunks does not duplicate vectors.

**Independent Test**: Add the same chunks twice; assert the store size is
unchanged.

**Acceptance Scenarios**:

1. **Given** ingested chunks, **When** they are added again, **Then** the vector
   count is unchanged (RD-2).

---

### Edge Cases

- **Empty query**: returns nothing.
- **No chunks**: returns nothing; no crash.
- **Embedding unavailable**: a provider error surfaces as a tool error, not a turn
  failure (RD-1).
- **Chroma not installed**: selecting a store provider that is not implemented
  fails loud at build (PB-1).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define an `Embedding` capability
  (`embed(texts) -> vectors`) with a keyless, deterministic provider and an
  OpenAI provider.
- **FR-002**: The system MUST define a `VectorStore` capability (upsert + cosine
  query) with an in-process provider; ingestion MUST be idempotent by chunk id
  (RD-2).
- **FR-003**: A dense `Retriever` provider MUST wire the two and implement the
  existing `Retriever` contract (`retrieve(query, k)`), returning chunks with a
  positive score, best first, with sources.
- **FR-004**: `knowledge.provider` MUST select `memory` (default) or `dense`;
  `embedding.provider` MUST select `hash` (default) or `openai`; an unknown value
  MUST fail loud (PB-1).
- **FR-005**: The keyless default path MUST be unchanged: with
  `knowledge.provider: memory`, no embedding or vector store is constructed.
- **FR-006**: Dense retrieval MUST require no API key with the `hash` embedding
  (P8).

### Key Entities

- **EmbeddingProvider**: turns text into fixed-dimension vectors.
- **VectorStore**: stores chunk vectors and answers nearest-neighbour queries.
- **DenseRetriever**: the `Retriever` implementation over the two.

## Observability

- The dense retriever is invoked by the existing `search_knowledge` tool, whose
  call is already traced as a `tool` span; the retrieved sources remain in the
  tool result (P4, OB-1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the dense provider, a returns query's top chunk is from
  `returns.md` (100% of the gold query).
- **SC-002**: The keyless embedding is deterministic across runs.
- **SC-003**: Re-ingesting does not change the vector count (idempotent).
- **SC-004**: The keyless default path is byte-for-byte unchanged (same chunks,
  same tool output shape).
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes.

## Assumptions

- The dense path is keyless by default via feature hashing; real semantic quality
  requires the OpenAI embedding provider (key).
- Chroma is deferred: its dependency tree (onnxruntime, grpcio, kubernetes, …) is
  too heavy for a keyless project; the `VectorStore` port leaves room for it.
- The corpus is tiny, so an in-process cosine store is sufficient.

## Measured Results

- Dense retrieval (keyless `hash` + in-memory vectors) closes the hard-query
  gap: hit-rate@3 **0.800 (TF-IDF) → 1.000 (dense)** on the 27-query benchmark.
- In-memory and Chroma stores agree on the top hit (parity).
- Source: `evals/bench.py`; aggregate: [`specs/RESULTS.md`](../RESULTS.md).

## Real-World Coverage

- **Input distribution**: retrieval queries; hard/paraphrase cases are measured.
- **Data quality**: chunk ids are stable; the vector store upsert is idempotent (RD-2).
- **Edge & failure modes**: empty query → nothing; an unknown provider fails loud (PB-1).
- **Scale envelope**: a tiny corpus; the system envelope is measured in `docs/scale.md`.
- **Degradation**: the keyless `hash` embedding needs no network; an embedding
  failure surfaces as a tool error.
- **Change evidence**: the retrieval benchmark measures the dense path (022).
