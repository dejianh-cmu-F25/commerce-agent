# Change safety: seams, blast radius, rollback

Constitution **SC-4** requires that changes be localized behind seams and that the
**blast radius** and the **migration / rollback path** be stated. No big-bang
rewrites.

## Seams

The system is built from ports and adapters, so a change to one provider does not
reach the others:

| Seam | Port | Adapters | Isolates |
| --- | --- | --- | --- |
| Model | `app/ports/llm.py` | `deepseek_client`, `mock_llm` | provider choice |
| Retrieval | `app/ports/retriever.py` | `retriever_memory`, `retriever_dense` | dense vs lexical |
| Embedding | `app/ports/embedding.py` | `embedding_hash`, `embedding_openai` | embedding choice |
| Vector store | `app/ports/vector_store.py` | `vector_memory`, `vector_chroma` | store choice |
| Storefront | `app/ports/storefront.py` | `storefront_memory`, `storefront_sqlite` | system of record |
| Memory | `app/ports/memory.py` | `memory_memory`, `memory_sqlite` | customer memory |
| Session | `app/ports/session_store.py` | in-memory, `session_sqlite` | persistence |
| Merchant | `app/ports/merchant.py` | `merchant_sqlite` | writes (gated, P3) |

Configuration is a contract (`app/core/settings.py`): a change is selected by
config (`PB-1`), so the blast radius of a provider change is the adapter plus its
config key — not the loop.

## Blast radius & rollback (per change)

Every entry in [`specs/change-log.json`](../specs/change-log.json) states:

- **Blast radius** — what the change can affect (a module behind a seam, a data
  set, a surface). The gate fails an entry that omits it.
- **Rollback** — how to undo it. The deployable unit is the app image; rollback
  is **`git revert` of the squash-merge commit + rebuild**. SQLite schema changes
  in this project are additive (`CREATE TABLE IF NOT EXISTS`), so a revert needs
  no destructive migration. A config-gated behavior (e.g. a fallback) can also be
  rolled back by flipping the key.

The gate enforces presence (`scripts/check_results.py`,
`scripts/check_change_evidence.py`); the [PR template](../.github/pull_request_template.md)
asks the author to state them.

## Gaps (honest)

- There is no automated rollback (no blue/green or canary); rollback is a manual
  revert + redeploy.
- A destructive schema migration has never been needed; if one is introduced, it
  must state its reverse explicitly here.
