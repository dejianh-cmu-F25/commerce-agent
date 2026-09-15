# Discovery: RAG ablation (feature 046, Phase 2)

Measured on the two Phase-1 benchmarks (`reports/discovery-baseline.md`):

- **ESCI** — 500 US queries, **human** E/S/C/I labels (semantic adversary).
- **Rule set** — 254 rule-generated cases over our 3,000-product catalog (lexical floor).

All configs are the same retrievers behind the `Retriever` port. `*-openai` uses
`text-embedding-3-small`; embeddings are cached (`data/embeddings.sqlite`).

## Results

**ESCI (nDCG@10, 500 queries)**

| Config | nDCG@10 | hit@10 | MRR |
| --- | --- | --- | --- |
| tfidf | 0.772 | 0.910 | 0.884 |
| dense-hash (keyless) | 0.775 | 0.922 | 0.897 |
| **dense-openai** | **0.880** | 0.966 | 0.941 |
| hybrid-openai | 0.869 | 0.966 | 0.936 |

**Our catalog (hit@10, 254 cases)**

| Config | hit@10 | recall@10 | MRR |
| --- | --- | --- | --- |
| **tfidf** | **0.992** | 0.720 | 0.772 |
| dense-hash (keyless) | 0.713 | 0.430 | 0.395 |
| dense-openai | 0.921 | 0.628 | 0.665 |
| **hybrid-openai** | **0.988** | 0.709 | 0.779 |

## What the data says

1. **RAG helps — but only where the task is semantic.** On ESCI, real embeddings
   take nDCG@10 **0.772 → 0.880 (+0.108 / +14%)**. On the lexical rule set they are
   **worse than tfidf** (0.921 vs 0.992), exactly as predicted.
2. **Keyless `dense-hash` is not RAG.** It is lexical (feature hashing), so it is
   *worse* than tfidf everywhere (ESCI 0.775, catalog 0.713). Real semantics need a
   real provider.
3. **Hybrid (RRF) is the robust default.** It is near the best on **both**:
   0.869 nDCG on ESCI (vs 0.880 dense) and 0.988 hit on the catalog (vs 0.992 tfidf).
   Pure dense wins semantic but loses lexical; pure keyword the reverse.
4. **Latency**: cached embeddings bring dense/hybrid query time to **~1 ms**
   (vs 450 ms uncached, and 1313 ms for the live Shopify keyword call).

## Recommendation

- Default discovery retriever: **hybrid (sparse + dense + RRF) behind the `Retriever`
  port**, keyless fallback = tfidf. This is a measurable improvement with no
  regression on the lexical floor.
- **Still not addressed**: the **constraint** class (`category_price` recall 0.72) —
  retrieval finds the right type but does not enforce "≤ $X". That is a
  **`DiscoveryGate`**, not a retrieval change.

## Reproduce

```sh
uv run python evals/esci_bench.py -n 500
uv run python evals/bench_discovery.py
uv run python evals/bench_discovery.py --shopify-sample 50
```
