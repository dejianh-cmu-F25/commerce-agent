# Discovery: second-stage reranking (feature 046, step A6)

**This is a 20-query probe, not the full set.** It was run first (as agreed) to see
whether reranking is worth measuring properly. Treat the deltas as a direction, not
a result.

- Retriever: `tfidf` (the shipped live retriever), reranker: **LLM listwise**
  (`deepseek-flash`), window **top-20** candidates, K=10.
- ESCI cases: **20** sampled from the 500-query set.

| | nDCG@10 | hit@10 | MRR |
| --- | ---: | ---: | ---: |
| retrieval only | 0.8086 | 0.9500 | 0.9250 |
| + LLM listwise rerank | **0.8444** | 0.9500 | **0.9500** |
| **Δ** | **+0.0358** | +0.0000 | **+0.0250** |

- **Cost**: ¥0.6506 for the 20 queries = **≈ ¥0.0325 per search** (derived from the
  cost meter's delta, not its cumulative total).
- **Latency**: **15 105 ms added per search** (~15 s; one listwise call in which the
  model emits the full permutation).
- **Unreachable**: **0/20** queries had a relevant item outside the top-20 window, so
  the window was not the binding constraint — the reranker had every candidate it
  could have used.

## Verdict

**The quality direction is positive but the latency disqualifies it for live search.**

1. The probe suggests reranking buys real ranking quality: nDCG@10 **+0.0358** and
   MRR **+0.0250**, with hit@10 unchanged (the reranker reorders what retrieval
   already found, which is exactly what the unreachable share of 0% predicts).
2. **15 seconds per search is not shippable inline.** A live search that adds 15 s to
   every query is worse than the ranking it improves. The honest use cases are the
   ones where latency is off the user's path: offline ranking, a batch re-rank, or an
   explicit async "refine these results" affordance.
3. **20 queries is too few to trust the delta.** nDCG@10 at n=20 moves by ~0.04 from
   sampling alone, so +0.0358 is *consistent with* an improvement rather than proof
   of one. Before it could be claimed, it needs the full 500-query set (about two
   hours at the observed pace, which is why the probe came first).

Recording this as a measured **deferral**: the reranker exists, is off by default
(`RERANK_ENABLED=false`), never breaks search (unparseable output, provider failure
and a hung call all fall back to the retrieval order — the hang was observed during
this probe and is now covered by a timeout and a test), and its cost is recorded
rather than hidden. Whether it ships is a latency decision, not a ranking one.
