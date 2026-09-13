# Agent Note: The large-corpus and long-session boundaries are measured

Status: implemented (2026-09-13) — feature `037-scale-boundaries`

## Problem

SC-1 requires the scale dimensions to be measured at the boundary, and the audit
named two residuals: "large-corpus (>10⁴ chunks) retrieval is untested" and "no
long-session (100+ turn) test". The envelope (feature 029) measured concurrency
but left data volume and session length unmeasured.

## Alternatives considered

- **Load a real 10k-document corpus.** Slow to fetch, license-encumbered, and the
  point is the data-structure cost, not content. Rejected.
- **A synthetic, representative corpus with unique ids.** Chosen: deterministic,
  free, and it isolates the retrieval cost at volume.
- **Assert time only for the long session.** Time is not the whole claim; the log
  must stay reconstructable (SL-1). Both are asserted.

## Decision

- **`evals/scale.py`** now measures:
  - **Large corpus**: retrieval over 10,000 synthetic chunks at the target
    concurrency; budget p95 ≤ 50,000 µs.
  - **Long session**: 100 scripted turns in one session; budget ≤ 5,000 ms, and
    `derive_messages` must succeed (the log is reconstructable, SL-1).
- Both are rendered in the report and gated; `docs/scale.md` documents them.

## Consequences

- The envelope now covers the two dimensions the audit called out. The measured
  cost is honest: retrieval over 10k chunks is ~7 ms p95 vs ~8 µs over 9 — the
  in-process scan is the boundary, and a vector store is the answer at volume.
- A 100-turn session completes in ~7 ms with 200 events and a reconstructable
  log; there is no super-linear blow-up.
- **Residual gaps**: catalogs >10k and concurrency >64 are not measured;
  multi-tenant isolation is untested.
