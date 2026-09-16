# Tasks: Product RAG — need-based discovery

**Feature**: `047-product-rag` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Delivered (P0) — this change

- [x] T001 Need dataset — `evals/need_cases.py` builds `evals/need_cases.jsonl`
  (24 cases; labels provable from the product's review/feature text; the builder
  fails loud if a cue is absent).
- [x] T002 Benchmark — `evals/need_bench.py`: keyless arms (`tfidf-plain`,
  `tfidf-enriched`, `dense-hash`); `--real` adds `dense-openai` / `hybrid-openai`;
  skips cleanly with no data; writes `evals/results-need.json`.
- [x] T003 Report — `reports/discovery-need.md` via `with_marker`, with the headline
  (keyword 0.292 → real embedding 0.583 hit@10, 2.0×).
- [x] T004 Evidence — a `specs/change-log.json` entry and `## Measured Results` in the
  spec.

## Planned (not part of this change)

These deepen the retrieval and are recorded here, not as open tasks of this PR
(P1/P2/P3/P4 in `spec.md` / `plan.md`):

- **P1 passage-level review index** — index each review as a `Chunk` (product id +
  review id) instead of truncating the top 3 to 200 chars; aggregate chunk hits to a
  product (max score). Config `catalog.passages: bool`; measure plain vs enriched vs
  passage; guardrail: the lexical rule set does not regress.
- **P2 query understanding** — port `app/ports/query_understanding.py` (need →
  terms/constraints); keyless `app/adapters/query_rules.py` + opt-in
  `app/adapters/query_llm.py` (HyDE-style); config `catalog.query_understanding:
  none|rules|llm` (fail loud on unknown); ablation off/on; cross-lingual slice
  (zh → en) reported honestly.
- **P3 grounded recommendation + judge** — the recommendation cites the product text it
  used; a judge scores the "grounded recommendation rate" (pattern from `evals/judge.py`);
  guardrail: no ungrounded recommendation.
- **P4 wire into the app** — `build_catalog_index`/`LocalSearchCatalog` honour the new
  config (tool schema unchanged); browser acceptance (a need query returns grounded
  product cards); finalize report, change-log, `docs/architecture.md` row, Agent Note.
