<!-- report-meta: generator=evals/need_bench.py cases=24 sources=evals/need_cases.jsonl,data/discovery/products.json fingerprint=e621f3900858 -->

# Product RAG: need-based discovery vs keyword search

A **need query** names a task or situation, not a product ("something to keep
dog hair off my clothes while grooming him"). The matching words live in the
**review / feature text**, so a title-only keyword index cannot serve it - which
is the gap measured here.

| Config | hit@10 | recall@10 | MRR | avg ms |
| --- | ---: | ---: | ---: | ---: |
| tfidf-plain | 0.292 | 0.292 | 0.110 | 1.2 |
| tfidf-enriched | 0.417 | 0.417 | 0.312 | 2.7 |
| dense-hash | 0.083 | 0.083 | 0.049 | 42.7 |
| dense-openai | 0.583 | 0.583 | 0.395 | 256.4 |
| hybrid-openai | 0.583 | 0.583 | 0.316 | 257.3 |

Reading: a title-only keyword index scores **0.292** hit@10; retrieving
over the product text (features + reviews) already scores **0.417** - the
capability a product RAG adds before any semantic embedding.

**Headline** - the best config (`dense-openai`) reaches **0.583** hit@10 vs the keyword baseline's **0.292** (**+0.292** absolute, **2.0×**): a real embedding, not just extra
words in the index, is what serves need queries.

## Method

- Cases: `evals/need_cases.jsonl`; each label is provable - the product's own
  text states it serves the need (`evals/need_cases.py` checks this).
- Metrics via `app/evaluation/retrieval_metrics.py` (hit@k / recall@k / MRR).
- `dense-hash` is keyless feature hashing (lexical), not semantics; run `--real`
  for a real embedding.

