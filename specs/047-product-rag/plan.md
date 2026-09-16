# Implementation Plan: Product RAG — need-based discovery

**Branch**: `047-product-rag` (stacked on `046-closed-loop`) | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

## Summary

Serve the **need-query** class in product discovery by retrieving over the product's
text (features + reviews), and prove the improvement over a keyword index on a
labeled set. P0 (dataset + benchmark + report) is delivered; P1–P4 build the
retrieval and query-understanding depth.

## Technical Context

**Language/Version**: Python 3.11 · **Dependencies**: existing (no new runtime dep) ·
**Storage**: the gitignored catalog snapshot + review SQLite · **Testing**: pytest +
keyless evals · **Target**: the discovery path behind `search_products`.

Reuses the existing seams: `Retriever`/`EmbeddingProvider`/`VectorStore` ports, the
`catalog_index` document builder, `retrieval_metrics`, `report_meta`, and the
`bench_discovery` retriever factory. No new model-facing tool.

## Constitution Check

- **P1** spec first — done (`spec.md`).
- **P3/P4** grounding: recommendations come only from tool results; ids only server-issued.
- **P5/PB-1/PB-2** the retrieval config and (P2) query understanding are selected by
  config; the query-understanding step is a port with a deterministic default.
- **P6** reuse the existing retriever/bench scaffolding; no new framework.
- **P7/EV** a labeled set, paired configs, guardrails, change-log entry.
- **RD-1** keyless lexical fallback for the dense leg.
- **RW/SC** `## Real-World Coverage` + a scale/latency statement.
- **TT** keyless gate stays green; the benchmark skips cleanly with no data.

## Project Structure — changes

```text
evals/need_cases.py         new  # build evals/need_cases.jsonl (labels provable from text)
evals/need_cases.jsonl      new  # 24 need cases (gitignored, like the other case sets)
evals/need_bench.py         new  # keyless + --real benchmark; writes reports/discovery-need.md
reports/discovery-need.md   new  # markered report
app/ports/query_understanding.py  P2  # need -> retrieval terms (protocol)
app/adapters/query_rules.py       P2  # keyless deterministic rewriting
app/adapters/query_llm.py         P2  # opt-in HyDE-style rewriting
app/adapters/catalog_index.py     P1  # passage-level review index (aggregate chunk -> product)
app/core/settings.py + config/settings.yaml  P1/P2  # catalog.query_understanding, catalog.passages
specs/047-product-rag/      spec, plan, tasks, review
```

**Structure Decision**: the change attaches to the documented discovery extension
point (`docs/architecture.md`); the loop, tools, and gates are untouched.

## Phases

1. **P0 (delivered)** — `need_cases.py` + `need_cases.jsonl` + `need_bench.py` + report.
2. **P1** — passage-level review index (each review = a chunk; aggregate to product),
   measured plain vs enriched vs passage.
3. **P2** — query understanding: a port + `rules` (keyless) / `llm` adapters; ablation
   off/on; cross-lingual slice.
4. **P3** — grounded recommendation + judge ("grounded-answer rate").
5. **P4** — wire the config into `build_catalog_index`/`LocalSearchCatalog`, agent
   demo, finalize report + change-log.

## Complexity Tracking

No constitution violations. The one new abstraction (P2 query understanding) is a
single-method port with a keyless default, justified by PB-2 (a capability with a
second plausible implementation) and P6 (the simplest seam that works).

## Risks & Rollback

- **Label circularity** — mitigated: labels are provable from text and evidence-linked;
  the query is phrased as a need (title overlap recorded per case).
- **Cost/latency** — keyless default; `--real` opt-in and cached.
- **Cross-lingual** — documented gap, measured separately (may be near zero).
- **Rollback** — additive; revert the merge; blast radius is discovery only.
