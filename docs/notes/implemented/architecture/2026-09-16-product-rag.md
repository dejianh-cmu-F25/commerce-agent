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
  cue is not in the product's review/feature text. 24 cases, 9 with zero title overlap.
- **A benchmark with an explicit control.** `evals/need_bench.py` runs a title-only
  keyword index (`tfidf-plain` — "traditional search"), the same lexical retriever over
  the full product text (`tfidf-enriched` — the cheapest RAG), keyless dense
  (`dense-hash`), and a real embedding (`dense-openai` / `hybrid-openai`), reporting
  hit@k / recall@k / MRR and latency.
- **Opt-in real model, keyless default.** The keyless arms run anywhere; `--real` uses
  the configured provider and is cached.
- **The result is the deliverable.** `reports/discovery-need.md` states the gap.

## Consequences

- The measured gap is real and large: need-query hit@10 **0.292 (keyword) → 0.417 (text
  retrieval) → 0.583 (real embedding), +0.292 / 2.0×**. Retrieving over the product
  text, and above all a real embedding, is what serves this class.
- The keyless `dense-hash` arm is *worse* than keyword (0.083), which keeps the earlier
  lesson honest: keyless hashing is not semantics.
- Later phases (passage-level review index, query understanding, a grounded-answer
  judge, cross-lingual) now have a benchmark to move; the spec records them as planned.
- Cost: one more markered report to keep fresh (`scripts/check_reports.py`).
