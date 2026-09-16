# Feature Specification: Product RAG — need-based discovery

**Feature Branch**: `047-product-rag`

**Created**: 2026-09-16

**Status**: In progress (P0 delivered; P1–P4 planned)

**Input**: A shopper asks with a **need** — a task or situation — not a product name
("something to keep dog hair off my clothes while grooming him"). Make product
discovery serve this query class by retrieving over the product's **text**
(description/features and reviews), and show, on a labeled set, the improvement over
traditional keyword search. This is the "product RAG" the project's discovery layer
was missing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover a product from a need, not a name (Priority: P1)

A shopper describes a task or situation; the agent retrieves candidate products from
the catalog's **text** (features + review evidence), not just their titles, and
recommends only products a tool returned.

**Why this priority**: it is the query class keyword search cannot serve, and the
largest share of "I don't know what it's called" shopping.

**Independent Test**: run `evals/need_bench.py` and read hit@10 for the keyword
baseline vs retrieval over the product text and a real embedding.

**Acceptance Scenarios**:

1. **Given** "something to keep dog hair off my clothes while grooming him", **When**
   the agent searches, **Then** the products it recommends are grounded in a tool
   result and the matching evidence is in the product's review/feature text.
2. **Given** a need no catalog product serves, **When** the agent searches, **Then**
   it recommends nothing rather than an unrelated item.

---

### User Story 2 - Labels a reviewer can verify (Priority: P2)

Every need case is labeled by evidence: the product is relevant because **its own
text states it serves the need**, and the builder checks this (`evals/need_cases.py`),
so the metric cannot be argued away.

**Why this priority**: an unverifiable label ("I think this is relevant") is not
evidence (EV).

**Independent Test**: `evals/need_cases.py` fails if a cue is absent from the
product's text.

**Acceptance Scenarios**:

1. **Given** a need case, **When** the builder runs, **Then** the evidence sentence
   exists in that product's review or feature text, or the build fails loud.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Discovery MUST retrieve over the product's **text** (title, vendor,
  type, tags, description/features, and cleaned review evidence), not titles alone.
- **FR-002**: A retrieval config MUST be selectable (lexical / dense / hybrid) and the
  chosen one recorded with the results; the keyless default MUST NOT need a key.
- **FR-003**: Every recommendation MUST be grounded: only ids a tool returned may be
  shown (P4), and the recommendation MUST be explainable from product text.
- **FR-004**: The comparison against traditional search MUST be measured on a labeled
  set with hit@k / recall@k / MRR, and reported with the corpus, sample size, model
  and date (`reports/discovery-need.md`, markered).
- **FR-005**: Query understanding (rewriting a need into retrieval terms) is a
  **replaceable capability**: a deterministic default (keyless) and an opt-in
  LLM path, selected by config (PB-1/PB-2), with the deterministic path as the
  fallback when the model is unavailable (RD-1). *(P2)*
- **FR-006**: No regression to the existing discovery/attribution benchmarks; the
  keyless gate stays green and downloads nothing (TT).
- **FR-007**: Retrieval MUST support **passage-level** indexing: each review/feature is
  a chunk carrying `metadata` (at least `product_id`, `source`, `category`, `price`,
  and for reviews `rating`/`verified`/`helpful_votes`), and chunk hits MUST aggregate
  back to a product (the link). The passage index MUST be selectable by config
  (`catalog.passages`), default off.
- **FR-008**: A **metadata filter** (`where`) MUST be applied at retrieval time
  (pre-filter before scoring/aggregation), with equality, `$in`, and range
  (`$gt/$gte/$lt/$lte`) operators; the document-level and in-memory paths MUST accept
  the same `where` shape as the Chroma path.

### Key Entities

- **NeedCase**: `case_id`, `need_type` (`task` | `attribute` | `gift` | `semantic`),
  `query`, `language`, `expected_ids[]`, `evidence`, `title_overlap_words[]`.
- **ProductDocument**: the searchable text of a product (plain | enriched).
- **QueryUnderstanding** *(planned)*: need → retrieval terms / constraints.

### Tool Contracts *(when the feature exposes tools to the model)*

No new model-facing tool: the change lives behind the existing `search_products`
(`app/tools/catalog.py`) and the `StorefrontBackend`/`Retriever` ports. `search_products`
keeps its schema (`query`, `limit`, `max_price`, `category`, `in_stock_only`,
`evidence`); the retrieval and query-understanding changes are selected by config.

## Real-World Coverage

- **Input distribution**: natural-language **need/task** phrasings, attribute queries,
  gift/situation queries, ambiguous requests, non-English input (a documented gap;
  measured separately), and adversarial/unanswerable needs. Unseen input falls back to
  the lexical retriever and the agent's clarify/redirect behaviour.
- **Data quality**: labels are provable from the corpus and validated at build time; a
  missing review store or snapshot degrades to the plain index (never crashes);
  `description` is marketing/feature text and reviews are the experiential evidence.
- **Edge & failure modes**: empty catalog/no snapshot → empty result; need with no
  matching product → recommend nothing; embedding outage → keyless lexical fallback
  (RD-1); oversized/agent-generated query → clamped; duplicate products → de-duped.
- **Scale envelope**: 3,000 products / 6,548 reviews; measured per-query latency is
  reported per config (`reports/discovery-need.md`); the keyless arms run in the gate.
- **Degradation**: the dense leg is behind `resilience.fallback_enabled`; a failed
  embedding or vector store falls back to the keyless lexical retriever and is traced.
- **Change evidence**: this feature touches retrieval → the before/after is recorded in
  `specs/RESULTS.md` and `specs/change-log.json`; the keyword baseline is the control.

## Evaluation Plan *(when the feature touches the model, prompt, retrieval, or data)*

- **Dataset(s)**: `evals/need_cases.jsonl` (24 hand-authored need queries, labels
  provable from product text); ESCI (`tasksource/esci`, Apache-2.0) for semantic
  ranking; the rule set for lexical regression.
- **Metric(s)**: hit@k, recall@k, MRR; **evidence-grounding rate** (the labeled
  evidence passage was retrieved); latency and cost. An LLM judge for reply grounding
  is deferred.
- **Threshold(s)**: the best config's need hit@10 MUST beat the keyword baseline by a
  measured, reported margin (current: **0.292 → 0.583, +0.292, 2.0×**); invariant
  guardrails (engine agreement, keyless gate) MUST NOT regress.
- **Slices**: by `need_type`; by `title_overlap_words` (pure needs = zero overlap); by
  language (English headline; cross-lingual as a separate slice, P2).
- **Cost/speed**: the keyless arms are free/fast; the `--real` arm uses a real
  embedding (cached) and is opt-in.
- **Report**: `reports/discovery-need.md`.

## Human-in-the-Loop *(when the feature performs or proposes a state change)*

n/a (no state change): discovery is read-only; the feature proposes nothing and writes
nothing. The existing return/checkout HITL is unaffected.

## Data Provenance & Licensing *(when the feature uses external data)*

| Source | Use | License | Retrieved |
| --- | --- | --- | --- |
| Amazon Reviews'23 item metadata | product catalog (`description` = feature list) | research dataset; not redistributed | — |
| Amazon Reviews'23 review text | review evidence in the enriched index | research dataset; not redistributed | — |
| Amazon ESCI (`tasksource/esci`) | semantic ranking labels | Apache-2.0 | — |
| `evals/need_cases.jsonl` | need labels | project (ours), evidence-linked | 2026-09-16 |

The need labels are **ours** and provable from the corpus; see `docs/data-provenance.md`.

## Non-Functional Requirements

- **Latency**: keyless need query ≤ ~5 ms (lexical); the `--real` embedding arm's
  latency is reported and bounded by the existing discovery envelope (`docs/scale.md`).
- **Cost**: the keyless default is free; `--real` is opt-in and cached.
- **Security & privacy**: no new PII; recommendations are grounded (P4).
- **Reliability**: a missing review store/snapshot degrades to the plain index; the
  dense leg has a keyless fallback (RD-1).

## Observability

`search_products` already emits a tool span; the retrieval config used is recorded
with the results in `evals/results-need.json`. Trace attributes unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The best retrieval config's need-query hit@10 is **≥ 2×** the keyword
  baseline on `evals/need_cases.jsonl` (met: keyword 0.206 → passage 0.735, 3.6×; 0.882 with a filter).
- **SC-002**: Retrieval over product text alone (no embedding) beats the title-only
  keyword index (met: 0.294 vs 0.206).
- **SC-003**: Every need label is provable from product text (builder fails otherwise).
- **SC-004**: The keyless gate stays green and downloads nothing.
- **SC-005**: Existing discovery benchmarks (rule set, ESCI, attribute) do not regress.
- **SC-006**: Passage-level indexing aggregates chunk hits to products and supports
  query-time metadata filters (met: filter `source=review` lifts hit@10 to 0.882).
- **SC-007**: The labeled evidence passage is retrieved for a majority of need cases
  (met: 0.676 with the passage embedding; the citation property of a grounded answer).
- **SC-008**: A Chinese need against the English catalog is served far better by a
  real embedding than by lexical search (met: zh hit@10 **0.000** keyword vs **0.600**
  passage+embedding).
- **SC-009**: A model recommendation drawn from the retrieved passages does not
  hallucinate a product or a quote (met: grounded rate **0.882** under the mechanical
  judge).

## Measured Results

Corpus: `evals/need_cases.jsonl` - **34 cases** (24 English + 10 Chinese, the
cross-lingual slice), labels provable from product text. Source:
`reports/discovery-need.md`, `evals/results-need.json`. Change log:
`specs/change-log.json`.

Need-query hit@10 over all 34 cases, by configuration:

| Config | hit@10 |
| --- | ---: |
| `tfidf-plain` (traditional keyword) | 0.206 |
| `tfidf-enriched` (document text) | 0.294 |
| `dense-hash` (keyless, lexical) | 0.059 |
| `dense-openai` (document, real embedding) | 0.500 |
| `chunks-tfidf` (passage) | 0.294 |
| **`chunks-dense-openai` (passage, real embedding)** | **0.735** |
| `chunks-dense-openai-llm` (HyDE rewrite, +2.1 s/query) | 0.706 |
| `chunks-dense-openai` + filter `source=review` | **0.882** |

**Language A/B** (a Chinese need against the English catalog) - lexical search
collapses, a real embedding over passages bridges it:

| config | en | zh |
| --- | ---: | ---: |
| `tfidf-plain` (traditional keyword) | 0.292 | **0.000** |
| `dense-openai` (document) | 0.583 | 0.300 |
| `chunks-dense-openai` (passage) | 0.792 | **0.600** |

Query-time metadata filters (passage index): `source=review` lifts hit@10 to
**0.882**; `source=description` drops to 0.235 (the evidence lives in reviews).

Query understanding (P2, measured): the rule extractor is **neutral** (0.735; none of
the cases carries a price) and the LLM rewrite is **slightly worse** (0.735 -> 0.706)
at **+2.1 s/query**, so `catalog.query_understanding` stays `none` by default.

Evidence grounding (P3, keyless): the labeled evidence passage is retrieved for
**0.676** of the cases with the passage embedding (vs 0.294 lexical) - the citation
property of a grounded answer.

Grounded answer (P3b, LLM judge, `--judge`): the model recommends from the retrieved
passages and quotes its evidence; the label is mechanical (the id must be retrieved,
the quote verbatim in a passage), so hallucination is **detected, not graded**:
grounded **0.882**, single-pick recall **0.441**, **¥0.22**. Choosing one product is
harder than retrieving it, which is why single-pick recall trails hit@10.

## Out of Scope

- Cross-lingual retrieval (中文 query → English catalog) — planned as a separate slice.
- Query rewriting / HyDE and the grounded-answer judge — planned (P2/P3).
- Reranker changes (the existing LLM reranker stays off by default).
- Any change to the post-purchase/returns path.

## Rollback & Versioning

- **Prompt**: n/a (no prompt change).
- **Model**: retrieval config selected by `settings.catalog`/`embedding.provider`;
  recorded with results.
- **Data**: catalog/reviews are gitignored, regenerated by their importers; the need
  case set is reproducible via `evals/need_cases.py`.
- **Rollback**: the feature is additive (a new benchmark + a doc index); reverting the
  merge restores the prior discovery path. Blast radius: discovery only.

## Assumptions

- The catalog snapshot and review store exist locally (gitignored, regenerated by
  their importers); the keyless gate runs without them.
- English need queries are the headline; cross-lingual is a documented, separate task.
- The embedding provider (opt-in) is the project's configured provider; the keyless
  default stays free.

## Known Gaps

- P0-P4 are delivered: data set + benchmark, passage index + filters, query
  understanding (measured neutral), the evidence-grounding metric, and the opt-in
  wiring (`catalog.passages`). The remaining, explicit gap is the **LLM judge** and
  **cross-lingual** retrieval (both optional, below).
- 24 cases is a start; the plan is to extend toward 60–100.
- The passage index and filters are measured in the benchmark; wiring them into the
  live `search_products` path is P4.
- Cross-lingual (zh → en) retrieval is documented as a gap, not implemented.
