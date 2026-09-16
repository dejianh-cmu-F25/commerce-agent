# Agent Note: Product RAG — measure need-based discovery against keyword

Status: implemented (2026-09-16) — feature `047-product-rag`

## Problem

Discovery had three benchmarks — the rule set (lexical), the attribute set (a review
phrase), and ESCI (semantic ranking) — but none for the query class where a shopper
names a **task or situation** rather than a product ("something to keep dog hair off
my clothes while grooming him"). The matching words there live in the **review or
feature text**, not the title, so this is exactly the class a title-only keyword index
cannot serve. Without a labeled set for it, "product RAG beats keyword search" was an
assertion, not a measurement.

## Alternatives considered

- **Reuse the attribute set.** It measures one phrase ("runs small"), not a situated
  need; it would not exercise a full-document retriever. Rejected as too narrow.
- **Derive need queries from review text verbatim.** Cheap, but the query then contains
  the review's own words, which is circular (it proves lexical, not retrieval).
  Rejected: the queries are authored as needs and the builder records the title overlap
  per case, so the pure-need cases are visible.
- **LLM-synthesised need queries.** A reasonable scale-up later, but it adds a labelling
  oracle we would then have to trust. Rejected for P0 in favour of hand-authored,
  evidence-linked labels.
- **Ship a new model-facing tool** (`find_products_for_need`). More surface for no
  capability the existing `search_products` cannot carry behind its ports. Rejected (P6).

## Decision

- **A need set whose labels are provable.** `evals/need_cases.py` finds the product by
  a unique title substring and the evidence sentence by a cue, and **fails loud** if the
  cue is not in the product's review/feature text. 34 cases (24 EN + 10 ZH), 9 with zero
  title overlap.
- **A benchmark with an explicit control.** `evals/need_bench.py` runs a title-only
  keyword index (`tfidf-plain` — "traditional search"), the same lexical retriever over
  the full product text (`tfidf-enriched` — the cheapest RAG), keyless dense
  (`dense-hash`), and a real embedding (`dense-openai` / `hybrid-openai`), reporting
  hit@k / recall@k / MRR and latency.
- **Opt-in real model, keyless default.** The keyless arms run anywhere; `--real` uses
  the configured provider and is cached; `--judge` adds the grounded-answer check.
- **The result is the deliverable.** `reports/discovery-need.md` states the gap.

## Consequences

- The measured gap is real and large: need-query hit@10 **0.206 (keyword) → 0.294 (text
  retrieval) → 0.500 (real embedding) → 0.735 (passage-level) → 0.882 (with a
  `source=review` filter)**. Retrieving over the product text, at passage granularity,
  with a real embedding, is what serves this class.
- The keyless `dense-hash` arm is *worse* than keyword (0.059), which keeps the earlier
  lesson honest: keyless hashing is not semantics.
- Query understanding is a **measured negative** and the grounded-answer judge is
  positive on grounding but trails retrieval on single-pick accuracy (both below).
- Cost: one more markered report to keep fresh (`scripts/check_reports.py`).

## Passage-level index and metadata filters (P1)

Follows the design every authoritative product-RAG stack uses (Google Agent Search
*Parse and chunk documents* + *Filter … metadata*; Azure AI Search *Vector Query
Filters*): content is **chunked**, each chunk is **linked to its product** by id, and a
query-time **metadata filter** narrows the candidates before scoring.

- **Chunks and the link.** `catalog_chunks` emits one chunk per review, one per feature
  sentence, and a product summary; every chunk carries `metadata` (`product_id`,
  `source`, `category`, `price`, `vendor`; reviews add `rating`/`verified`/
  `helpful_votes`). `PassageCatalogIndex` aggregates chunk hits to a product by best
  passage score - the "documents are returned by aggregating chunks into documents"
  shape, and it keeps the hits so an answer can cite the evidence it used.
- **Filters.** A `where` clause filters on `Chunk.metadata` with equality, `$in`, and
  range operators (`app/core/filters.py`); the in-memory stores and retrievers apply it
  directly and Chroma receives the same shape (`to_chroma_where`). The ports gained it
  **additively** (`where=None` default), so nothing else changes.
- **Result.** Passage-level retrieval lifts need hit@10 **0.500 → 0.735**; a
  `source=review` filter (the evidence kind these needs live in) lifts it to **0.882**,
  and `rating>=4` to **0.912** - a filter here is a precision win, not a cost. Filtering
  to features-only drops to 0.235, which is the honest other side: the filter must match
  the passage kind.
- Cost: the keyless passage index is ~5× the document index (16,035 chunks vs 3,000
  products) and ~9 ms/query; the dense passage index is ~1.5 s/query with a real
  embedding. That trade is stated in the report, not hidden.

## Query understanding (P2) - a measured negative

The hypothesis was that rewriting a need into retrieval terms (HyDE-style) would
recover recall the passage embedding missed, and that a rule could extract hard
constraints. Both were built and measured, and **neither helped**:

- `chunks-dense-openai` **0.735**; `+rules` **0.735**; `+llm` **0.706** (hit@10).
- The rule extractor was narrowed to a **price ceiling only**: an earlier version also
  guessed a category from a trailing "in X", which read "healthy in summer" as
  `category=Summer` and **lowered** hit@10. A regression test pins the fix. A rule that
  reads intent is a rule that will be wrong.
- The LLM rewrite returned a different query but retrieved **slightly worse** than the
  original (0.735 → 0.706) at **+2.1 s/query** - on this corpus the need queries are
  already descriptive and the passage embedding already matches the evidence text, so
  there is no headroom for a rewrite to add.
- Correction worth recording: the first run reported the rewrite as exactly neutral,
  but a JSON-brace bug in `config/prompts/query_rewrite.md` made `.format()` raise, so
  the adapter silently fell back to the original query every time. Once fixed the
  rewrite actually ran - and was slightly *worse*. A "neutral" that looks too clean is
  worth an audit of the path, not a conclusion.

Kept anyway, off by default: the port is a clean seam and the LLM adapter has a
deterministic fallback (RD-1), so a deployment whose queries *are* short and whose
corpus is formal (the Elastic "HyDE" case) can turn it on and re-measure. But the
default is `none`, because a model call with no measured lift is a cost, not a feature.

## Evidence grounding (P3) - the citation property, keyless

A recommendation that is grounded in *what a review or feature says* must actually
surface that passage; a product hit alone does not prove the reason. So the benchmark
also measures the fraction of need cases whose labeled **evidence** sentence was
retrieved: **0.294 (chunk-tfidf) → 0.676 (chunk-dense-openai)**. It is deterministic and
model-free, which is why it is the cheap reproducible part.

## Grounded answer (P3b) - the judge made mechanical

The LLM judge is the half that is usually not reproducible, so its label was made
mechanical: the model recommends a product **from the retrieved passages** and quotes
its evidence, and the check is that the recommended id is one of the retrieved products
**and** the quote appears **verbatim** in a retrieved passage. Hallucination is therefore
*detected, not graded* - no hand labels, no self-report. Prompt:
`config/prompts/grounded_answer.md` (PB-4); run with `--judge`.

- **Grounded 0.882** - the model does not invent a product or a quote.
- **Single-pick recall 0.441** - choosing the *one* best product is harder than
  retrieving it (hit@10 0.735), which is the honest ceiling a generator faces that a
  retriever does not.
- ¥0.22 for 34 cases.

## Cross-lingual (P-lang) - lexical collapses, passages bridge

The catalog and its reviews are English; a shopper may not be. Ten of the needs were
translated to Chinese and run against the English catalog:

| config | en | zh |
| --- | ---: | ---: |
| `tfidf-plain` (keyword) | 0.292 | **0.000** |
| `tfidf-enriched` (document text) | 0.417 | **0.000** |
| `dense-openai` (document embedding) | 0.583 | 0.300 |
| `chunks-dense-openai` (passage embedding) | 0.792 | **0.600** |

Lexical search matches on words, so a Chinese query against English text scores
**0.000** - it is not a quality gap, it is a total miss. A real (multilingual)
embedding recovers part of it (0.300), and **passage-level** retrieval recovers most
(0.600): the short review passages give the query a tighter semantic target than a
long flattened document. This is the honest answer to "can RAG serve a Chinese
shopper over an English catalog": yes, through the embedding, and better at passage
granularity - without translating the catalog.
