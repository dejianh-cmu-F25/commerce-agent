# Research: Knowledge Retrieval

## D1. Provider

**Decision**: an in-memory TF-IDF retriever (pure Python). No embeddings, no
vector store, no new dependency.

**Rationale**: keyless and reproducible (P8); the `Retriever` port lets a dense
provider (Chroma) replace it later.

**Alternatives considered**: Chroma + OpenAI embeddings (rejected for now: adds a
heavy dependency and a paid provider); BM25 (rejected: TF-IDF is sufficient for a
tiny corpus).

## D2. Chunking

**Decision**: split each markdown file on blank lines into paragraphs; skip
paragraphs shorter than `min_chars`; chunk id = `"{source}#{index}"` (stable, so
re-ingestion is idempotent, RD-2).

## D3. Scoring

**Decision**: lowercase tokenization (`[a-z0-9]+`), TF-IDF with cosine-ish
normalization; return the top-k by score, dropping zero scores.

## D4. Tool

**Decision**: `search_knowledge(query, k)` returns a readable list of snippets
with sources; the agent cites the source. No component (renders as a tool step).

## D5. Wiring

**Decision**: `build_retriever(settings)` loads the docs at startup; the tool is
registered only when the retriever has chunks (otherwise `search_knowledge` still
works and returns "no results").
