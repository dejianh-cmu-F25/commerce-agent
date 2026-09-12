# Browser checkpoint: 012-knowledge-retrieval

Constitution SR-4 / SR-5. The knowledge tool is user-visible, so a checkpoint is
recorded.

## Card

```
Checkpoint: 012 knowledge retrieval
URL:    http://127.0.0.1:8000
Steps:
  1. Ask "What is your return policy?".
  2. Confirm the search_knowledge step runs and the answer is grounded.
Review:
  - [x] search_knowledge is called
  - [x] the answer cites the returns document (30-day window)
  - [x] no console errors
Clauses: P4, PB-1, PB-2, RD-2, WV-5
Features: 012
```

## Result

- Date: 2026-09-13
- Status: **PASS**
- Evidence: `specs/012-knowledge-retrieval/checkpoint.png`

| Check | Result |
| --- | --- |
| `search_knowledge` tool step runs | pass |
| Answer states the 30-day return window (grounded in `returns.md`) | pass |
| Answer mentions the refund process | pass |
| Console errors | 0 |

## Notes

- The retriever is keyless (in-memory TF-IDF); no embeddings service or new
  dependency (P8).
- Ingestion is idempotent by stable chunk id (RD-2); a missing knowledge
  directory yields an empty retriever.
- A dense provider (Chroma) can replace the memory provider behind the same
  `Retriever` port later.
