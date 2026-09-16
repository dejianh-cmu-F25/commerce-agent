<!-- report-meta: generator=evals/need_bench.py cases=24 sources=evals/need_cases.jsonl,data/discovery/products.json fingerprint=e621f3900858 -->

# Product RAG: need-based discovery vs keyword search

A **need query** names a task or situation, not a product ("something to keep
dog hair off my clothes while grooming him"). The matching words live in the
**review / feature text**, so a title-only keyword index cannot serve it - which
is the gap measured here.

| Config | hit@10 | recall@10 | MRR | avg ms |
| --- | ---: | ---: | ---: | ---: |
| tfidf-plain | 0.292 | 0.292 | 0.110 | 1.3 |
| tfidf-enriched | 0.417 | 0.417 | 0.312 | 2.7 |
| dense-hash | 0.083 | 0.083 | 0.049 | 43.4 |
| chunks-tfidf | 0.417 | 0.417 | 0.231 | 11.2 |
| dense-openai | 0.583 | 0.583 | 0.395 | 260.6 |
| hybrid-openai | 0.583 | 0.583 | 0.316 | 259.5 |
| chunks-dense-openai | 0.792 | 0.792 | 0.539 | 1394.7 |
| chunks-dense-openai-rules | 0.792 | 0.792 | 0.539 | 1395.2 |
| chunks-dense-openai-llm | 0.792 | 0.792 | 0.539 | 1390.5 |

Reading: a title-only keyword index scores **0.292** hit@10; retrieving
over the product text (features + reviews) already scores **0.417** - the
capability a product RAG adds before any semantic embedding.

**Headline** - the best config (`chunks-dense-openai`) reaches **0.792** hit@10 vs the keyword baseline's **0.292** (**+0.500** absolute, **2.7×**).
Passage-level retrieval (each review/feature as a linked chunk) over a
real embedding is what closes the gap; a metadata filter sharpens it
further still.

Best filter: `chunks-dense-openai:reviews-only` reaches **0.917** hit@10 (vs 0.292 keyword): restricting to the passage kind that carries the
evidence is a precision win, not a cost.

## Query-time metadata filters (passage index)

The passage index stores each review/feature as a chunk with metadata; a
`where` clause restricts the candidates before aggregation (feature 047).

| filter | hit@10 |
| --- | ---: |
| chunks-tfidf:reviews-only | 0.542 |
| chunks-tfidf:high-rating | 0.458 |
| chunks-tfidf:features-only | 0.083 |
| chunks-dense-openai:reviews-only | 0.917 |
| chunks-dense-openai:high-rating | 0.917 |
| chunks-dense-openai:features-only | 0.292 |

A filter trades recall for precision: it only counts products that have a
matching passage, which is what a shopper means by "only reviews" or
"only 4★ and up".

## Query understanding (measured, not assumed)

Rewriting a need into retrieval terms (`-llm`, HyDE-style) and rule-based
constraint extraction (`-rules`) were run against the same passage index.

| config | hit@10 |
| --- | ---: |
| chunks-dense-openai (none) | 0.792 |
| chunks-dense-openai-rules | 0.792 |
| chunks-dense-openai-llm | 0.792 |

**Negative result, reported as such.** Neither step beats the passage
embedding alone on this set: the rewritten query and the original both
retrieve the same passages, and the rule extractor only helps when a
constraint is stated (none of these needs carries one). A model call with
no measured lift is a cost, not a feature - so `query_understanding` stays
`none` by default and the rewrite is opt-in.
| chunks-tfidf:reviews-only | 0.542 |
| chunks-tfidf:high-rating | 0.458 |
| chunks-tfidf:features-only | 0.083 |
| chunks-dense-openai:reviews-only | 0.917 |
| chunks-dense-openai:high-rating | 0.917 |
| chunks-dense-openai:features-only | 0.292 |

A filter trades recall for precision: it only counts products that have a
matching passage, which is what a shopper means by "only reviews" or
"only 4★ and up".

## Method

- Cases: `evals/need_cases.jsonl`; each label is provable - the product's own
  text states it serves the need (`evals/need_cases.py` checks this).
- Metrics via `app/evaluation/retrieval_metrics.py` (hit@k / recall@k / MRR).
- `dense-hash` is keyless feature hashing (lexical), not semantics; run `--real`
  for a real embedding.
- `chunks-*` configs index each review/feature as a passage and aggregate chunk
  hits back to a product (`app/adapters/catalog_index.py:PassageCatalogIndex`).

