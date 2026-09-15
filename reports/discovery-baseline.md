# Discovery baseline (feature 046, Phase 1)

Measured **before** any RAG work, so a later change has a real before → after.
All numbers are keyless and reproducible (`data/` is gitignored; rebuild with the
two scripts).

## A. ESCI (external, human-labelled semantics)

Amazon Shopping Queries Dataset (`tasksource/esci`, Apache-2.0), **US locale**,
**500 queries randomly sampled** (`seed=0`) from the 12,624 usable queries in the
first test shard. Candidates ranked per query; gains E=1, S=0.1, C=0.01, I=0
(Amazon KDD Cup 2022 mapping).

| Config | nDCG@10 | hit@10 | MRR | avg |
| --- | --- | --- | --- | --- |
| tfidf | **0.772** | 0.910 | 0.884 | 0.01 ms |
| dense-hash | **0.775** | 0.922 | 0.897 | 0.16 ms |

→ **Semantic headroom ≈ 0.23 nDCG.** The keyless `hash` embedding (lexical) is
not better than tfidf; a **real** embedding is the lever.

## B. Our catalog (rule-generated, lexical/structured)

254 cases built from the real 3,000-product catalog by deterministic rules
(the answer is derivable from the data, so the set cannot favour a retriever).

| Config | hit@10 | recall@10 | MRR | avg | note |
| --- | --- | --- | --- | --- | --- |
| tfidf | **0.992** | 0.720 | 0.772 | 0.6 ms | keyless lexical |
| dense-hash | 0.713 | 0.430 | 0.395 | 43.5 ms | keyless, **worse** |
| shopify-keyword | 0.920 | 0.920 | 0.796 | **1313.7 ms** | the **live** retriever |

By rule (hit@10):

| Rule | tfidf | dense-hash |
| --- | --- | --- |
| title_substring | 1.000 | 0.733 |
| brand | 1.000 | 0.387 |
| colour | 1.000 | 0.960 |
| category_price | 0.931 | 0.862 |

> `shopify-keyword` was sampled on the first 50 cases (all `title_substring`), so
> it has one rule row only.

## C. Failure classification (which lever to pull)

| Class | Evidence | Lever |
| --- | --- | --- |
| **Semantic retrieval** | ESCI nDCG 0.772 (rule set is 0.992) → the gap is *semantics*, not matching | **RAG (real embedding)** |
| **Constraint** | `category_price` recall@10 0.720 while hit@10 0.931: retrieval finds the right *type* but does not enforce "≤ $X" | **`DiscoveryGate`** (structured filter) |
| **Coverage** | journey `discovery-23` ("a tent"): no tent in the catalog | **data**, not code |
| **Formulation** | journey `policy-09` answered without `search_knowledge` | **prompt / query rewriting** |
| **Latency** | live retriever 1313.7 ms/query vs local tfidf 0.6 ms | local retriever as a **cache/shortlist** stage |

## D. What this tells us about RAG

1. On **lexical/structured** queries, keyword/tfidf is already at the ceiling
   (0.99) — **RAG would not help there**, and keyless `dense-hash` is *worse*.
2. The **only** measured headroom is **semantic** (ESCI 0.77, and UK/US phrasing),
   which needs a **real embedding provider**.
3. The live retriever is **~2000× slower** than the local one and slightly less
   accurate — a local retriever could serve as a **shortlist stage** regardless of RAG.

**Conclusion (Phase 2 options):** run the ablation
**A** keyword · **B** query-rewriting · **C** RAG(real embedding) · **D** C+B on
**both** benchmarks, and add a **`DiscoveryGate`** for the constraint class.
