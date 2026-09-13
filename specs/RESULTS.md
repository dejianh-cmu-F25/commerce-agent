# Measured Results

The canonical, reproducible record of what this project measured and what each
change contributed. Each feature spec carries a `## Measured Results` section
with its slice; this file aggregates them.

**Provenance**

| Field | Value |
| --- | --- |
| Date | 2026-09-13 |
| Agent model | `deepseek-flash` |
| Rendered prompt hash | `8578920a4f16` |
| Judge model | `deepseek-chat` |
| Seeds | 3 |
| Embedding | keyless `hash` (256 dims) |
| Vector stores | `memory`, `chroma` |
| Source | `evals/report.md` |

**Reproduce**

- Keyless (in the gate): `make ci-fast` runs `evals/bench.py` and
  `evals/ablation.py`, then renders `evals/report.md` via
  `uv run python evals/report.py --write`.
- Real model (opt-in, snapshot): `uv run python evals/agent_eval.py --real
  --seeds 3`. These numbers are a **dated snapshot** and are **not** regenerated
  by the gate.
- Budget: **¥0.5764 / ¥10.00** spent across all runs (harness-enforced, HR-12).

## Retrieval benchmark (keyless)

27 labeled queries (easy / medium / hard) over `config/knowledge/`; k = 3.
hit-rate@3 = at least one expected document in the top 3; recall@3 = fraction of
expected documents found; MRR = mean reciprocal rank of the first hit.

| Config | hit-rate@3 | recall@3 | MRR | hard hit@3 |
| --- | ---: | ---: | ---: | ---: |
| `tfidf` | 0.963 | 0.963 | 0.926 | 0.800 |
| `dense-hash` | 1.000 | 1.000 | 0.907 | 1.000 |
| `dense-chroma` | 1.000 | 1.000 | 0.907 | 1.000 |

## Feature ablation (keyless)

The same 12 gold scenarios under each configuration; the delta is vs the naked
baseline.

| Config | Passed | Pass rate | Delta vs naked |
| --- | ---: | ---: | ---: |
| `naked` | 9/12 | 0.750 | +0.000 |
| `+memory` | 11/12 | 0.917 | +0.167 |
| `+skills` | 10/12 | 0.833 | +0.083 |
| `+dense-hash` | 9/12 | 0.750 | +0.000 |
| `+dense-chroma` | 9/12 | 0.750 | +0.000 |

## Agent reliability (real, 6 templates × 3 seeds = 18 runs)

| Pass@1 | Pass@k | Best@k | Pass^k |
| ---: | ---: | ---: | ---: |
| 0.778 | 1.000 | 1.000 | 0.667 |

Per template:

| Template | Pass@1 | Pass@k | Pass^k |
| --- | ---: | ---: | ---: |
| `budget_search` | 0.333 | 1.000 | 0.000 |
| `multi_item_cart` | 0.333 | 1.000 | 0.000 |
| `add_named_item` | 1.000 | 1.000 | 1.000 |
| `policy_question` | 1.000 | 1.000 | 1.000 |
| `refuse_out_of_window` | 1.000 | 1.000 | 1.000 |
| `ungrounded_rejected` | 1.000 | 1.000 | 1.000 |

## Process metrics (real, per run)

| steps | tool ok/err | ungrounded | avg ms | p95 ms | prompt tok | completion tok | cache hit | cost CNY |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2.06 | 37/0 | 0 | 3550 | 5485 | 73491 | 8218 | 64000 | 0.0949 |

## Failure attribution (real)

| Category | Count |
| --- | ---: |
| `incomplete` | 4 |

## Rubric judge (real, 18 graded, 0 vetoes)

| Dimension | Avg (1-4) |
| --- | ---: |
| grounding | 3.89 |
| correctness | 3.89 |
| policy_compliance | 4.00 |
| completeness | 3.39 |
| tone | 4.00 |

## Deployment smoke (feature 015)

Keyless container smoke (`scripts/smoke_container.sh`, image `commerce-agent:ci`):

```
healthz: ok
readyz:  {"status":"ready","storefront":"memory","memory":"memory"}
spa:     ok
chat:    ok
user:    uid 10001 (non-root)
```

## Quality gate

- `make ci-fast`: **PASS** (ruff + format, pyright, pytest, evals, retrieval
  benchmark, feature ablation, spec self-review, agent notes, frontend
  lint/typecheck/test/build).
- Tests: **131 passed**.
- Gold scenarios: **12/12**.
- Agent notes: **16** valid.

## Feature → effect

| Change | Effect (measured) |
| --- | --- |
| Customer memory (013) | Ablation +0.167 pass rate on the gold set |
| Skills (019) | Ablation +0.083 pass rate on the gold set |
| Dense retrieval (018) | Hard-query hit-rate@3 0.800 → 1.000 (TF-IDF → dense) |
| Chroma vector store (021) | Parity with the in-memory store; hard hit@3 1.000 |
| Guardrails (020) | 0 ungrounded-id attempts in the real run |
| Evaluation upgrade (023–024) | Real Pass@1 0.778 / Pass^k 0.667; 0 judge vetoes; ¥0.0949 per 18 runs |
