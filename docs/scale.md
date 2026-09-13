# Scale envelope & SLOs

Constitution **SC-1** requires the system to state the scale dimensions it must
survive and the **measured** behavior at that boundary; **SC-3** requires
latency, error, and cost budgets to be declared and tracked, with regressions
visible. This document is the canonical declaration; `evals/scale.py` measures it
and the gate enforces it.

## Scale dimensions (current envelope)

| Dimension | Tested value | Source |
| --- | ---: | --- |
| Catalog products | 5 | `app/adapters/catalog_seed.py` |
| Knowledge chunks | 9 | `config/knowledge/` |
| Concurrent operations | 1 / 4 / 16 / 64 | `evals/scale.py` |
| Ops per level | 64 | `evals/scale.py` |
| Session length | 24 turns | `agent.max_turns` |
| Cost | ¥10 total cap | `data/budget.json` (HR-12) |

These are the **tested** dimensions. Larger catalogs, corpora, and concurrency are
an explicit, documented gap (see "Boundary" below).

## SLOs (declared budgets)

| SLO | Budget (at concurrency 16) | Metric |
| --- | ---: | --- |
| Retrieval latency | p95 ≤ **2000 µs** | TF-IDF, in-process |
| Turn latency | p95 ≤ **10000 µs** | full scripted agent turn |
| Error rate | **0.00** | failed ops / total |
| Cost | **¥10.00** | harness-enforced (HR-12) |

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
- **Beyond it**: throughput is capped by a single process/GIL; the web server
  scales by running multiple workers/processes, each with its own storefront
  connection. SQLite is embedded (DP-6); concurrent writers are serialized.
- **Known gaps**: no multi-tenant isolation test, no long-session (100+ turn)
  memory test, no large-corpus (>10⁴ chunks) retrieval test. These are the next
  scale work; they are not claimed here.
