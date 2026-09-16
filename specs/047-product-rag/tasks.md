# Tasks: Product RAG — need-based discovery

**Feature**: `047-product-rag` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Delivered (P0) — dataset, benchmark, report

- [x] T001 Need dataset — `evals/need_cases.py` builds `evals/need_cases.jsonl`
  (24 cases; labels provable from the product's review/feature text; the builder
  fails loud if a cue is absent).
- [x] T002 Benchmark — `evals/need_bench.py`: keyless arms (`tfidf-plain`,
  `tfidf-enriched`, `dense-hash`); `--real` adds `dense-openai` / `hybrid-openai`;
  skips cleanly with no data; writes `evals/results-need.json`.
- [x] T003 Report — `reports/discovery-need.md` via `with_marker`, with the headline.
- [x] T004 Evidence — a `specs/change-log.json` entry and `## Measured Results` in the
  spec.

## Delivered (P1) — passage index, product link, metadata filters

- [x] T101 `Chunk.metadata` + a metadata filter (`app/core/filters.py`) with equality,
  `$in` and range operators; the same `where` shape across the in-memory stores,
  the retrievers, and Chroma (`to_chroma_where`).
- [x] T102 Ports: `VectorStore.query(..., where)` and `Retriever.retrieve(..., where)`
  (additive; default `None` preserves the old behaviour).
- [x] T103 Passage index — `app/adapters/catalog_index.py:catalog_chunks` (one chunk per
  review/feature, each with metadata) and `PassageCatalogIndex` (chunk hits aggregated
  to a product; the link). Benchmark arms `chunks-tfidf` / `chunks-dense-openai`.
- [x] T104 Measured: passage + real embedding **0.792** hit@10; filter `source=review`
  **0.917** (vs keyword 0.292).

## Delivered (P2) — query understanding (measured neutral)

- [x] T201 Port `app/ports/query_understanding.py` (`QueryPlan` + `QueryUnderstanding`).
- [x] T202 Keyless `app/adapters/query_rules.py` (price-ceiling extraction only; a
  category guess false-positived on "in summer" and was removed, with a regression test).
- [x] T203 Opt-in `app/adapters/query_llm.py` (HyDE-style rewrite + price extraction),
  prompt in `config/prompts/query_rewrite.md` (PB-4), metered, timeout-bounded, and a
  deterministic fallback on failure (RD-1).
- [x] T204 Config `catalog.query_understanding: none|rules|llm` + `CATALOG_QUERY_UNDERSTANDING`
  (>`.env.example` parity) + `config/settings.yaml`.
- [x] T205 Measured: neither rewrite nor rules beat the passage embedding alone
  (**0.792 → 0.792**); `none` stays the default. Negative result reported in
  `reports/discovery-need.md`.

## Planned (not part of this change)

- **Cross-lingual slice (zh → en)** — documented gap; a multilingual embedding or a
  translate step, measured separately.
- **P3 grounded recommendation + judge** — the recommendation cites the passage it
  used (the chunk is already returned); a judge scores the "grounded recommendation
  rate" (pattern from `evals/judge.py`); guardrail: no ungrounded recommendation.
- **P4 wire into the app** — `build_catalog_index`/`LocalSearchCatalog` honour the new
  config (`catalog.passages`, filters) with the tool schema unchanged; pre-filter
  (Azure's recommended default) as the mode; browser acceptance; finalize the report,
  change-log, `docs/architecture.md` row, Agent Note.
