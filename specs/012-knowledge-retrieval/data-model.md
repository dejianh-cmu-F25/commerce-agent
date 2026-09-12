# Data Model: Knowledge Retrieval

## Chunk (`app/core/types.py`)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | `"{source}#{index}"` (stable) |
| `text` | `str` | the paragraph |
| `source` | `str` | the file name (e.g. `returns.md`) |
| `score` | `float` | retrieval score (0 outside `retrieve`) |

## Config (`KnowledgeSettings`)

| Field | Type | Default |
| --- | --- | --- |
| `provider` | `"memory"` | `"memory"` |
| `path` | `str` | `"./config/knowledge"` |
| `top_k` | `int` | `3` |
| `min_chars` | `int` | `40` |

Env overrides: `KNOWLEDGE_PROVIDER`, `KNOWLEDGE_PATH`.

## Knowledge docs (seed)

| File | Covers |
| --- | --- |
| `shipping.md` | delivery times, costs, free-shipping threshold |
| `returns.md` | return window, condition, refund timing |
| `warranty.md` | warranty length and what it covers |

## Tool result

`search_knowledge` returns text: `[source] snippet` lines, top-k, or "No relevant
knowledge found."
