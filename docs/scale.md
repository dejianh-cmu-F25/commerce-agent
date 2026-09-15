# Scale envelope & SLOs

Constitution **SC-1** requires the system to state the scale dimensions it must
survive and the **measured** behavior at that boundary; **SC-3** requires
latency, error, and cost budgets to be declared and tracked, with regressions
visible. This document is the canonical declaration; `evals/scale.py` measures it
and the gate enforces it.

## Scale dimensions (current envelope)

| Dimension | Tested value | Source |
| --- | ---: | --- |
| Catalog products | 5 (and a synthetic **5,000**) | `app/adapters/catalog_seed.py`, `evals/scale.py` |
| Knowledge chunks | 9 (and a synthetic **10,000**) | `config/knowledge/`, `evals/scale.py` |
| Concurrent operations | 1 / 4 / 16 / 64 | `evals/scale.py` |
| Ops per level | 64 | `evals/scale.py` |
| Session length | 24 turns cap; **100 turns** measured | `agent.max_turns`, `evals/scale.py` |
| Cost | metered per run (no in-app cap by default) | `data/budget.json` (HR-12) |

These are the **tested** dimensions. Larger catalogs and higher concurrency are an
explicit, documented gap (see "Boundary" below).

## SLOs (declared budgets)

| SLO | Budget (at concurrency 16) | Metric |
| --- | ---: | --- |
| Retrieval latency | p95 ≤ **2000 µs** | TF-IDF, in-process |
| Turn latency | p95 ≤ **10000 µs** | full scripted agent turn |
| Large-corpus retrieval | p95 ≤ **50000 µs** | TF-IDF over 10,000 chunks |
| Large-catalog search | p95 ≤ **50000 µs** | SQLite storefront, 5,000 products |
| Long-session | ≤ **5000 ms** | 100 turns, reconstructable log (SL-1) |
| Error rate | **0.00** | failed ops / total |
| Cost | per-run CNY reported | metered (HR-12); the hard limit is the deployment's |

The latency budgets are **regression guards with large headroom**: the keyless
stack measures in the tens of microseconds, so a breach means an order-of-magnitude
regression (an accidental network call, a blocking sleep, an O(n²) loop), not
normal noise on a loaded host. They bound harness overhead, **not** provider
latency — the real-model eval (`evals/agent_eval.py --real`) measures that.

## Measured behavior

`evals/scale.py` runs the keyless stack at each concurrency level and reports p50,
p95, throughput, and error count; the numbers are rendered into
[`evals/report.md`](../evals/report.md) (`## Scale & SLOs`) and the gate fails on a
breach at the target concurrency. Run it directly:

```bash
uv run python evals/scale.py
```

## Boundary & degradation

- **Within the envelope** (≤ 64 concurrent keyless ops): error rate 0, latency
  flat — the stack is CPU-bound and GIL-bound, not I/O-bound.
- **Data volume**: retrieval over 10,000 chunks is ~7 ms p95 vs ~8 µs over 9 —
  the cost is in the in-process scan, so a large corpus is the first thing to feel
  the boundary. A vector store (dense retrieval) is the intended answer at volume.
- **Catalog volume**: storefront search over 5,000 products is ~15 ms p95 — the
  search reads, normalizes, and ranks the whole catalog per query (O(catalog)); a
  large catalog is the second boundary. An index (FTS/SQL filter) is the answer.
- **Session length**: 100 turns complete in ~7 ms with a reconstructable log; the
  log grows linearly (2 events/turn) and there is no O(n²) re-derivation.
- **Beyond it**: throughput is capped by a single process/GIL; the web server
  scales by running multiple workers/processes, each with its own storefront
  connection. SQLite is embedded (DP-6); concurrent writers are serialized.
- **Known gaps**: no multi-tenant isolation test; catalogs >10k and concurrency
  >64 are not measured. These are the next scale work; they are not claimed here.
