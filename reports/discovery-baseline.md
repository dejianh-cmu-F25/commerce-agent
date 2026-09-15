<!-- report-meta: generator=evals/bench_discovery.py (hand-written summary) cases=216 sources=evals/discovery_cases.jsonl,data/esci/cases.json,evals/bench_discovery.py fingerprint=ecdd5e503510 -->

# Discovery baseline (feature 046, Phase 1) — re-baselined

Measured **before** any RAG work, so a later change has a real before → after.
All numbers are reproducible (`data/` is gitignored; rebuild with the two scripts).

> **Superseded numbers.** The first version of this report measured section B on a
> **254-case** file. The rule generator now de-duplicates by query, so the file is
> **216 cases** and the old rule-set figures (`tfidf hit@10 0.992 / recall@10 0.720`,
> `shopify-keyword 1313.7 ms`) are **not comparable** and must not be quoted. The
> ESCI figures (section A) are unaffected: that query set did not change.

## A. ESCI (external, human-labelled semantics)

Amazon Shopping Queries Dataset (`tasksource/esci`, Apache-2.0), **US locale**,
**500 queries randomly sampled** (`seed=0`) from the 12,624 usable queries in the
first test shard. Candidates ranked per query; gains E=1, S=0.1, C=0.01, I=0
(Amazon KDD Cup 2022 mapping). Full ablation in `reports/discovery-rag.md`.

| Config | nDCG@10 | hit@10 | MRR |
| --- | --- | --- | --- |
| tfidf | 0.772 | 0.910 | 0.884 |
| dense-hash (keyless) | 0.775 | 0.922 | 0.897 |
| dense-openai | **0.880** | 0.966 | 0.941 |
| hybrid-openai | 0.869 | 0.966 | 0.936 |

→ **Semantic headroom ≈ 0.11 nDCG** (0.772 → 0.880) and the keyless `hash`
embedding (lexical) is **not** better than tfidf; a **real** embedding is the lever.

## B. Our catalog (rule-generated, lexical/structured) — 216 cases

Built from the real 3,000-product catalog by deterministic rules (the answer is
derivable from the data, so the set cannot favour a retriever). De-duplicated by
query: a repeated query would silently weight the average.

| Config | hit@10 | recall@10 | MRR | avg | note |
| --- | --- | --- | --- | --- | --- |
| **tfidf** | **0.991** | **0.817** | 0.820 | **0.6 ms** | keyless lexical |
| hybrid-openai | 0.986 | 0.803 | **0.824** | 258.3 ms | RRF (sparse+dense) |
| dense-openai | 0.907 | 0.718 | 0.717 | 258.2 ms | embeddings **lose** here |
| shopify-keyword | 0.920 | 0.920 | 0.796 | **1361.5 ms** | the **live** retriever |

By rule (hit@10):

| Rule | tfidf | hybrid-openai | dense-openai |
| --- | --- | --- | --- |
| title_substring | 1.000 | 0.987 | 0.933 |
| brand | 1.000 | 1.000 | 0.907 |
| colour | 1.000 | 1.000 | 0.865 |
| category_price | 0.931 | 0.931 | 0.897 |

### Reading `recall@10` honestly

`recall@10` averages **per-case** ratios, and 74% of cases have exactly **one**
expected id, so it is dominated by them. The correct ceiling for this set is the
mean of the per-case ceilings, `mean(min(n,10)/n)` = **0.902** (not the
ratio-of-sums 0.604, which is the wrong statistic for a mean of ratios).

tfidf at 0.817 is therefore at **91% of the achievable recall**, and the residual
is concentrated in the 20% of cases with more than 10 expected ids.

> `shopify-keyword` was sampled on the first 50 cases (all `title_substring`, so
> mostly single-answer) — its row is a latency and sanity check, not a like-for-like
> comparison with the full-set configs.

## C. Failure classification (which lever to pull)

| Class | Evidence | Lever |
| --- | --- | --- |
| **Semantic retrieval** | ESCI nDCG@10 0.772 (rule set 0.991) → the gap is *semantics*, not matching | **real embeddings** (already measured: 0.880) |
| **Constraint** | `category_price` recall limited while hit@10 0.931: retrieval finds the right *type* but does not enforce "≤ $X" | **`DiscoveryGate`** (structured filter) |
| **Coverage** | journey `discovery-23` ("a tent"): no tent in the catalog | **data**, not code |
| **Formulation** | journey `policy-09` answered without `search_knowledge` | **prompt / query rewriting** |
| **Latency** | live retriever 1361.5 ms/query vs local tfidf 0.6 ms | local retriever as a **cache/shortlist** stage |

## D. What this tells us about RAG

1. On **lexical/structured** queries, keyword/tfidf is already at the ceiling
   (0.991) — **RAG would not help there**, and a dense retriever alone is *worse*
   (0.907); the keyless `dense-hash` was worse still.
2. The measured headroom is **semantic** (ESCI 0.772 → 0.880 with a real
   embedding), which is a **different corpus and metric**.
3. The live retriever is **~2100× slower** than the local one and less accurate on
   hit@10 (0.920 vs 0.991) — a local retriever is a win **regardless of RAG**.
4. `hybrid-openai` buys the best MRR (0.824) at 258 ms/query (a query embedding
   call per search), so the **choice of retriever for the live path is a latency
   decision**, and it should be re-measured once documents get richer (features +
   review evidence, where the semantic half earns its keep).

**Conclusion:** wire the **local retriever** into the live discovery path
(measured: faster and more accurate), keep tfidf as the default until richer
documents justify the semantic half, and add a **`DiscoveryGate`** for the
constraint class.
