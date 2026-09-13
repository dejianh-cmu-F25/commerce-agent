# Degradation & fallbacks

Constitution **RD-1** requires that every external dependency and LLM-enhanced
step have a deterministic fallback, that it be disableable by config, and that the
system **degrade observably rather than fail silently**.

## Declared fallbacks

| Dependency | Primary | Fallback | Observable | Config |
| --- | --- | --- | --- | --- |
| Knowledge retrieval | dense (embeddings + vector store) | keyless lexical (`InMemoryRetriever`) | `FallbackRetriever.degraded` + `degradations` | `resilience.fallback_enabled` |
| Knowledge corpus | `config/knowledge/` | empty (no crash) | empty result | — |
| Customer memory | SQLite store | no memory (turn proceeds) | traced span, error swallowed | — |
| Merchant writes | SQLite | staged change only (never applied) | `P3` gate | — |
| LLM provider | configured provider | fallback provider (if configured), else a surfaced error turn | `FallbackLLM.degraded` + `ErrorEvent` | `llm.fallback_provider` |
| Budget | — | turn stopped at the cap (HR-12) | `BudgetExceeded` event | `budget.enabled` |

The **retriever** fallback is the one wrapped by code: `app/core/resilience.py`
composes a primary and a secondary retriever, serves the secondary on a primary
failure, records a `Degradation`, and does **not** retry a failed primary (so an
outage does not add a timeout to every query). `web/main.py` wires
dense → lexical when `resilience.fallback_enabled` is true (the default).

## Observable, not silent

A silent `except: pass` is forbidden. Every fallback either records a
`Degradation`, emits an event, or is traced — so an operator can see that the
system is running degraded, not broken. The coverage is measured keylessly by
`evals/fallbacks.py` and rendered into `evals/report.md`.

```bash
uv run python evals/fallbacks.py
```

## Gaps (honest)

- The LLM fallback serves only when the primary fails **before the first token**;
  a mid-stream failure surfaces (a partial answer cannot be un-sent). With no
  `llm.fallback_provider` configured, the LLM failure degrades to a surfaced error.
- The embedding provider has no separate fallback from the retriever: a dense
  failure is handled at the retriever level (embedding → lexical).
- Degradations are recorded in-process, not yet exported as a metric/counter.
