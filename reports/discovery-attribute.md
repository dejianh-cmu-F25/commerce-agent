<!-- report-meta: generator=evals/bench_attribute.py --write cases=28 sources=evals/attribute_cases.jsonl,evals/bench_attribute.py fingerprint=eccc3cd5d348 -->

# Discovery: what review enrichment buys (feature 046, steps C/D/E)

- Attribute queries: **28**, each labelled by the review text that
  contains the attribute (evals/attribute_cases.py) - no human judgement.
- Same 3,000-product snapshot in both modes; K=10.

| Config | documents | hit@10 | recall@10 | MRR | avg |
| --- | --- | ---: | ---: | ---: | ---: |
| `tfidf` | plain | 0.179 | 0.179 | 0.033 | 0.6 ms |
| `tfidf` | enriched | 0.893 | 0.893 | 0.520 | 1.1 ms |
| `bm25` | plain | 0.071 | 0.071 | 0.043 | 0.8 ms |
| `bm25` | enriched | 0.786 | 0.786 | 0.406 | 1.5 ms |
| `hybrid-openai` | plain | 0.143 | 0.143 | 0.038 | 618.0 ms |
| `hybrid-openai` | enriched | 0.714 | 0.714 | 0.360 | 267.7 ms |

## What this says

- `tfidf`: hit@10 0.179 -> 0.893 (**+0.714**) on attribute queries.
- `bm25`: hit@10 0.071 -> 0.786 (**+0.714**) on attribute queries.
- `hybrid-openai`: hit@10 0.143 -> 0.714 (**+0.571**) on attribute queries.

Read this together with the rule set, where the same enrichment costs hit@10 0.991 -> 0.954. Enrichment is not a general improvement: it trades lexical precision for attribute recall, which is why the shipped document stays plain until a deployment knows its query mix (or keeps two indexes).

## Which default? The query-mix arithmetic

Enrichment is a trade, so the shipped default depends on how often the attribute class
occurs. Blending the two measured sets (lexical rule set 0.991 -> 0.954; attribute
0.179 -> 0.893):

| Attribute share of queries | plain documents | enriched documents |
| ---: | ---: | ---: |
| 5% | 0.950 | **0.951** |
| 10% | 0.910 | **0.948** |
| 15% | 0.869 | **0.945** |
| 30% | 0.747 | **0.936** |
| 50% | 0.585 | **0.923** |

The crossover sits near **5%**, so the shipped configuration enables enrichment
(`catalog.enrich: true`) while the library default stays `false`, and the benchmark
keeps both modes runnable.

**Caveats, stated rather than buried:** the attribute set is small (28 cases) and its
share in a real store is an assumption, not a measurement; the rule set is synthetic
lexical queries; and neither set contains the mixed queries real shoppers type. The
honest next step, if the mix matters, is **routing**: keep both indexes and send a
query to the one its class belongs to, which the two measured sets now justify.
