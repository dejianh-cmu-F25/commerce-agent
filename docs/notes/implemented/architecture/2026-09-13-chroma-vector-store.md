# Agent Note: Chroma is the default vector store; memory is the keyless fallback

Status: implemented (2026-09-13) — feature `021-chroma-vector-store`

## Problem

Feature 018 added the dense retrieval path but deferred Chroma because of its
dependency weight, leaving the in-memory store as the only vector backend. The
maintainer wants a real vector database for the project, and Chroma is the
choice. The question is how to add it without breaking the keyless, reproducible
default and without surprising behavior.

## Alternatives considered

- **Keep Chroma deferred (018's decision).** Rejected by the maintainer: a real
  vector DB is wanted.
- **Run Chroma as a separate server (compose service).** More production-like, but
  adds a service and network dependency to a single-command demo. Rejected:
  embedded `PersistentClient` matches DP-1/DP-6.
- **Let Chroma compute embeddings with its default model.** Convenient, but it
  downloads all-MiniLM and introduces a second embedding path that disagrees with
  our `EmbeddingProvider`. Rejected: we supply vectors and disable the default EF.
- **Change the code default to Chroma.** Would make every test build Chroma (slow,
  writes to disk). Rejected: code default stays `memory`; the shipped
  `settings.yaml` selects `chroma`.

## Decision

- **`ChromaVectorStore` behind the existing `VectorStore` port.** Persistent
  embedded client, cosine space, `score = 1 - distance`, non-positive scores
  filtered; upsert keyed by chunk id (idempotent, RD-2); `source` kept as
  metadata.
- **No downloads, no telemetry.** The default embedding function is disabled
  (the harness passes vectors), and `anonymized_telemetry=False`.
- **The shipped config defaults to dense + Chroma.** `settings.yaml` sets
  `knowledge.provider: dense` and `vector_store.provider: chroma`; the code
  defaults remain `memory` so tests and the keyless path are fast and
  dependency-light.
- **`chromadb` is a base dependency.** One `uv sync` makes it available to the
  app, the image, and the tests (accepted trade-off).

## Consequences

- The demo uses a real, persistent vector DB; data lives in `./data/chroma` (a
  mounted volume), so it survives restarts (DP-6).
- The keyless path is preserved: `vector_store.provider: memory` + `knowledge
  .provider: memory` need no Chroma, and the container smoke sets
  `KNOWLEDGE_PROVIDER=memory`.
- Chroma import adds startup time and the dependency tree is heavy; this is the
  cost of a real vector DB, accepted deliberately.
- This supersedes the "Chroma is deferred" decision in the 018 note.
