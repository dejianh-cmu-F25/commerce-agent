<!-- report-meta: generator=evals/need_bench.py cases=34 sources=evals/need_cases.jsonl,data/discovery/products.json fingerprint=654fb67c1490 -->

# Product RAG: need-based discovery vs keyword search

A **need query** names a task or situation, not a product ("something to keep
dog hair off my clothes while grooming him"). The matching words live in the
**review / feature text**, so a title-only keyword index cannot serve it - which
is the gap measured here.

| Config | hit@10 | recall@10 | MRR | avg ms |
| --- | ---: | ---: | ---: | ---: |
| tfidf-plain | 0.206 | 0.206 | 0.078 | 0.9 |
| tfidf-enriched | 0.294 | 0.294 | 0.221 | 2.0 |
| dense-hash | 0.059 | 0.059 | 0.034 | 43.8 |
| chunks-tfidf | 0.294 | 0.294 | 0.163 | 8.0 |
| dense-openai | 0.500 | 0.500 | 0.293 | 314.2 |
| hybrid-openai | 0.500 | 0.500 | 0.237 | 259.6 |
| chunks-dense-openai | 0.735 | 0.735 | 0.487 | 1386.0 |
| chunks-dense-openai-rules | 0.735 | 0.735 | 0.487 | 1389.0 |
| chunks-dense-openai-llm | 0.735 | 0.735 | 0.487 | 1387.5 |

Reading: a title-only keyword index scores **0.206** hit@10; retrieving
over the product text (features + reviews) already scores **0.294** - the
capability a product RAG adds before any semantic embedding.

**Headline** - the best config (`chunks-dense-openai`) reaches **0.735** hit@10 vs the keyword baseline's **0.206** (**+0.529** absolute, **3.6×**).
Passage-level retrieval (each review/feature as a linked chunk) over a
real embedding is what closes the gap; a metadata filter sharpens it
further still.

Best filter: `chunks-dense-openai:high-rating` reaches **0.912** hit@10 (vs 0.206 keyword): restricting to the passage kind that carries the
evidence is a precision win, not a cost.

## Language A/B (Chinese needs vs the English catalog)

The catalog and its reviews are English, so a Chinese need query is the honest
cross-lingual test (feature 047, P-lang). Lexical search matches on words and
collapses; a real embedding may bridge the gap semantically.

| config | en | zh |
| --- | ---: | ---: |
| tfidf-plain | 0.292 | 0.000 |
| tfidf-enriched | 0.417 | 0.000 |
| dense-openai | 0.583 | 0.300 |
| chunks-dense-openai | 0.792 | 0.600 |

## Query-time metadata filters (passage index)

The passage index stores each review/feature as a chunk with metadata; a
`where` clause restricts the candidates before aggregation (feature 047).

| filter | hit@10 |
| --- | ---: |
| chunks-tfidf:reviews-only | 0.382 |
| chunks-tfidf:high-rating | 0.324 |
| chunks-tfidf:features-only | 0.059 |
| chunks-dense-openai:reviews-only | 0.882 |
| chunks-dense-openai:high-rating | 0.912 |
| chunks-dense-openai:features-only | 0.235 |

A filter trades recall for precision: it only counts products that have a
matching passage, which is what a shopper means by "only reviews" or
"only 4★ and up".

## Query understanding (measured, not assumed)

Rewriting a need into retrieval terms (`-llm`, HyDE-style) and rule-based
constraint extraction (`-rules`) were run against the same passage index.

| config | hit@10 |
| --- | ---: |
| chunks-dense-openai (none) | 0.735 |
| chunks-dense-openai-rules | 0.735 |
| chunks-dense-openai-llm | 0.735 |

**Negative result, reported as such.** Neither step beats the passage
embedding alone on this set: the rewritten query and the original both
retrieve the same passages, and the rule extractor only helps when a
constraint is stated (none of these needs carries one). A model call with
no measured lift is a cost, not a feature - so `query_understanding` stays
`none` by default and the rewrite is opt-in.
| chunks-tfidf:reviews-only | 0.382 |
| chunks-tfidf:high-rating | 0.324 |
| chunks-tfidf:features-only | 0.059 |
| chunks-dense-openai:reviews-only | 0.882 |
| chunks-dense-openai:high-rating | 0.912 |
| chunks-dense-openai:features-only | 0.235 |

A filter trades recall for precision: it only counts products that have a
matching passage, which is what a shopper means by "only reviews" or
"only 4★ and up".

## Evidence grounding

A recommendation grounded in *what a review or feature says* must surface
that passage. This is the fraction of need cases whose labeled evidence
sentence was retrieved - the citation property of a product-RAG answer,
measured without a model (feature 047, P3):

| config | evidence retrieved |
| --- | ---: |
| chunks-tfidf | 0.294 |
| chunks-dense-openai | 0.676 |

## Method

- Cases: `evals/need_cases.jsonl`; each label is provable - the product's own
  text states it serves the need (`evals/need_cases.py` checks this).
- Metrics via `app/evaluation/retrieval_metrics.py` (hit@k / recall@k / MRR).
- `dense-hash` is keyless feature hashing (lexical), not semantics; run `--real`
  for a real embedding.
- `chunks-*` configs index each review/feature as a passage and aggregate chunk
  hits back to a product (`app/adapters/catalog_index.py:PassageCatalogIndex`).

