# Agent Note: Dense retrieval is keyless by default; Chroma is deferred

Status: implemented (2026-09-13) — feature `018-dense-retrieval`

## Problem

The retrieval path was lexical only (TF-IDF). Adding a dense path raised three
cross-cutting questions:

1. **How do we embed without a key?** A real embedding model needs a provider and
   an API key, which breaks the keyless, reproducible default (P8).
2. **Where does the vector store live?** Chroma is the obvious choice, but its
   dependency tree is heavy.
3. **How do the pieces compose?** Retrieval must stay a single capability the
   `search_knowledge` tool consumes (P4, PB-2).

## Alternatives considered

- **Bundle Chroma as a hard dependency.** Chroma 1.5 pulls ~31 runtime deps
  (onnxruntime, grpcio, kubernetes, opentelemetry-*, tokenizers, …). That bloats
  every install and contradicts the keyless/simple stance (P6, P8). Deferred: the
  `VectorStore` port is the seam for it later.
- **Make the OpenAI embedding the default.** Best semantic quality, but needs a
  key and spends money; the default must be keyless. Rejected.
- **Skip dense entirely and keep TF-IDF.** Cheapest, but the backlog explicitly
  wanted a dense path. Rejected.
- **An async embedding port.** Cleaner for the network provider, but it would
  ripple through the sync `Retriever` contract and the tool. Rejected for now;
  the keyless provider is instant, and the OpenAI path is documented as blocking.

## Decision

- **Two new ports.** `EmbeddingProvider.embed(texts) -> vectors` and
  `VectorStore` (upsert + cosine query, keyed by chunk id).
- **Keyless dense default.** `HashEmbeddingProvider` (feature hashing with
  `hashlib`) is deterministic, dependency-free, and needs no key; `openai` is the
  opt-in semantic upgrade. `embedding.provider: hash` and
  `vector_store.provider: memory` are the defaults.
- **One retriever seam.** `DenseRetriever` wires the two and implements the
  existing `Retriever` contract; `knowledge.provider: memory|dense` selects the
  path, and the `search_knowledge` tool is unchanged.
- **Idempotent ingestion.** Chunks are keyed by id, so re-adding is a no-op
  (RD-2).

## Consequences

- The default install stays keyless and light; semantic quality requires opting
  into `embedding.provider: openai` (and a key).
- Chroma is not implemented: selecting `vector_store.provider: chroma` fails loud
  (PB-1) with a clear message. Adding it later is a new `VectorStore` provider,
  no core change.
- The OpenAI embedding path blocks the event loop during a query; acceptable for
  the demo corpus, and the first thing to make async if it matters.
- The `Retriever` port now includes `add`, so ingestion is part of the capability
  rather than a provider-only method.
