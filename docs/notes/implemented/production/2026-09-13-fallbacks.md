# Agent Note: Dependencies degrade through declared fallbacks

Status: implemented (2026-09-13) — feature `031-fallbacks`

## Problem

Some paths degraded (a missing knowledge dir returned empty; memory errors were
swallowed; the budget stopped a turn), but not every dependency had a *declared*
fallback. A dense-retrieval failure — an embedding or Chroma outage — raised out
of the knowledge tool with no defined behavior. RD-1 was only partially met, and
"degrades" was implicit, not stated or measured.

## Alternatives considered

- **Try/except inside the knowledge tool.** Scatters the policy and makes it
  untestable in isolation. Rejected.
- **A second LLM provider as fallback.** Doubles the surface and the cost; the
  loop already surfaces an LLM failure observably. Rejected.
- **A generic `FallbackRetriever` wrapper + a coverage benchmark.** Chosen.

## Decision

- **`app/core/resilience.py`**: `FallbackRetriever` composes a primary and a
  secondary, serves the secondary on a primary failure, records a `Degradation`
  (component, primary, fallback, reason), and **does not retry a failed primary**
  — an outage must not add a timeout to every query.
- **Config-gated**: `resilience.fallback_enabled` (default on). Set false and the
  primary's failure propagates — the fallback is a choice, not a hidden surprise.
- **Wired dense → keyless lexical** in `build_retriever`; the lexical retriever is
  the keyless default, so the degraded mode is a legitimate one (trades recall for
  availability).
- **Measured**: `evals/fallbacks.py` exercises five dependency cases (retriever
  fallback, healthy, disabled, missing knowledge, LLM failure); coverage goes
  from **0.400** (only the pre-existing degradations) to **1.000**.

## Consequences

- A vector-store or embedding outage now serves lexical results and records the
  degradation, instead of failing the knowledge tool.
- Degradation is visible (`degraded`, `degradations`) and documented
  (`docs/degradation.md`), not silent.
- **Residual gaps**: the LLM has no second provider (its failure surfaces as an
  error turn, which RD-1 accepts as observable); degradations are recorded
  in-process, not yet exported as a counter/metric.
