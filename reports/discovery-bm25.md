<!-- report-meta: generator=evals/bench_discovery.py --document plain (hand-written summary) cases=216 sources=evals/discovery_cases.jsonl,evals/bench_discovery.py,app/adapters/retriever_bm25.py fingerprint=f526d1a5e494 -->

# Discovery: BM25 as the lexical leg (feature 046, step A8)

BM25 is the default lexical scorer in most search stacks, so the honest question is
not "is it good?" but "is it better *here*?" This measures it as a drop-in
replacement for the TF-IDF leg, on the same 216-case rule set and the same K=10.

| Config | hit@10 | recall@10 | MRR | avg |
| --- | ---: | ---: | ---: | ---: |
| **tfidf** (shipped) | **0.991** | **0.817** | 0.820 | **0.6 ms** |
| bm25 | 0.968 | 0.804 | **0.856** | 0.8 ms |
| hybrid-openai | 0.986 | 0.803 | 0.824 | 265.6 ms |
| hybrid-bm25 | 0.972 | 0.798 | 0.812 | 265.4 ms |

By rule (hit@10):

| Rule | tfidf | bm25 |
| --- | ---: | ---: |
| title_substring | 1.000 | 0.987 |
| brand | 1.000 | 1.000 |
| colour | 1.000 | 0.946 |
| category_price | 0.931 | 0.862 |

## What this says

1. **BM25 loses where the rule set measures recall.** hit@10 0.991 → 0.968 and
   recall@10 0.817 → 0.804. The loss is concentrated in `colour` and
   `category_price` — exactly the rules with **several** valid answers, so a drop in
   "found at least one" shows up in both metrics.
2. **BM25 wins on order.** MRR 0.820 → **0.856**: when the answer is a single item,
   BM25 tends to put it higher. Saturation and length normalisation help with
   *ranking*; they cost *recall* on this corpus.
3. **The corpus explains it.** Our documents are short and near-uniform
   (`title + vendor + type + tags`), which is precisely the regime where length
   normalisation has little to correct, while TF-IDF's raw term emphasis keeps
   multi-answer queries covered. The theory predicts a small, ambiguous effect —
   and that is what the measurement shows, in both directions at once.
4. **Replacing the leg is not justified**, so the shipped sparse leg stays `tfidf`.
   The finding is recorded because "BM25 by default" is a habit, not a measurement:
   here it trades 2.3 points of hit@10 for 3.6 points of MRR, on the same data.

`bm25` remains available (`retrieval.sparse: bm25`, and a `hybrid-bm25` benchmark
config), so the swap is one config line the day a corpus arrives where length
normalisation earns its keep.
