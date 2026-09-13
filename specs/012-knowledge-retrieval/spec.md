# Feature Specification: Knowledge Retrieval

**Feature Branch**: `012-knowledge-retrieval`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a `Retriever` port with a keyless in-memory TF-IDF provider over
policy docs in `config/knowledge/`, ingested by paragraph chunks; add a
`search_knowledge` tool so the agent answers policy questions from grounded
snippets with sources.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Answer policy questions from documents (Priority: P1)

A customer asks a policy question (shipping, returns, warranty). The agent calls
`search_knowledge`, gets grounded snippets with their source documents, and
answers from them.

**Why this priority**: Grounding (P4) extends beyond the catalog to store policy;
without it the agent would invent policies.

**Independent Test**: Retrieve for a query and assert the top chunk comes from the
expected document.

**Acceptance Scenarios**:

1. **Given** ingested policy docs, **When** the customer asks about returns,
   **Then** the tool returns a snippet from `returns.md` and the answer cites it.
2. **Given** a query with no match, **When** the tool runs, **Then** it returns
   nothing and the agent says it does not know.

---

### User Story 2 - Keyless and config-selected (Priority: P1)

The retriever is chosen by configuration and needs no provider or network.

**Independent Test**: Build the retriever with each provider; assert the memory
provider loads the docs; assert an unknown provider is rejected.

**Acceptance Scenarios**:

1. **Given** `knowledge.provider: memory`, **When** the app starts, **Then** the
   docs are ingested and searchable.
2. **Given** an unknown provider, **When** settings load, **Then** it fails loud.

---

### User Story 3 - Idempotent, chunked ingestion (Priority: P2)

Docs are chunked by paragraph; re-ingesting does not duplicate chunks.

**Independent Test**: Ingest twice; assert the chunk count is unchanged.

**Acceptance Scenarios**:

1. **Given** ingested docs, **When** ingestion runs again, **Then** the chunk
   count is unchanged (RD-2).

### Edge Cases

- An empty or missing knowledge directory: an empty retriever (no error).
- Very short paragraphs: skipped below a minimum length.
- A query that matches only stop words: no results.

## Requirements *(mandatory)*

- **FR-001**: A `Retriever` port MUST define `retrieve(query, k) -> list[Chunk]`.
- **FR-002**: A keyless in-memory provider MUST implement it (TF-IDF over
  tokenized chunks); no external service or new dependency (P8).
- **FR-003**: Ingestion MUST load `config/knowledge/*.md`, split by paragraph,
  and be idempotent (chunk ids stable; re-ingest adds nothing) (RD-2).
- **FR-004**: `search_knowledge(query)` MUST return the top-k chunks with their
  `source` document (P4).
- **FR-005**: The agent's answer MUST be able to cite the source document.
- **FR-006**: The provider MUST be selected by `config/settings.yaml` and
  validated; an unknown provider MUST fail loud (PB-1).
- **FR-007**: A missing knowledge directory MUST yield an empty retriever, not an
  error.
- **FR-008**: The chat surface MUST be unchanged apart from the new tool.

### Key Entities

- **Chunk**: `id`, `text`, `source`, `score`.
- **Retriever**: the capability (retrieve).
- **KnowledgeSettings**: `provider` (`memory`), `path`, `top_k`, `min_chars`.

## UI States *(convention, WV-6)*

The browser surface is unchanged (the tool result renders as a tool step).

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty / Streaming / Success / Error | As in 003 | Unchanged; a `search_knowledge` step appears |

## Web Acceptance *(convention, WV-1)*

Open `/`, ask "what is your return policy?". The `search_knowledge` step runs and
the answer cites the returns document.

## Observability *(convention, WV-1)*

Knowledge turns emit the existing spans (007); the `search_knowledge` tool span
records the query and the number of hits. No new events.

## Success Criteria *(mandatory)*

- **SC-001**: A policy query returns the correct document's chunk (unit test).
- **SC-002**: Re-ingestion does not duplicate chunks.
- **SC-003**: A missing knowledge directory yields an empty retriever.
- **SC-004**: The retriever is keyless and adds no dependency.

## Assumptions

- Policy docs are small markdown files under `config/knowledge/`.
- Dense embeddings + a vector store (Chroma) are a later feature; this is a
  keyless lexical retriever behind the same `Retriever` port.
- Chunks are paragraphs; no overlap.

## Real-World Coverage

- **Input distribution**: policy questions; the 27-query benchmark includes hard
  and paraphrase cases. Adversarial queries are not covered (gap).
- **Data quality**: markdown docs chunked by paragraph; chunk ids are stable and
  re-ingestion is idempotent (RD-2).
- **Edge & failure modes**: empty query → no hits; no match → the agent says it does not know.
- **Scale envelope**: a tiny policy corpus; not measured (gap).
- **Degradation**: a missing knowledge directory yields an empty retriever.
- **Change evidence**: retrieval changes are measured by `evals/bench.py` (022).
