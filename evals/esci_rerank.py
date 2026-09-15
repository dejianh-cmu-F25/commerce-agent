#!/usr/bin/env python3
"""Does a second-stage reranker improve ESCI ranking? (feature 046, step A6)

ESCI is where first-stage retrieval still has room (nDCG@10 0.772 tfidf / 0.880
with real embeddings), so it is the honest place to test a reranker — the rule set
is saturated and could only ever show noise.

The measurement is deliberately conservative:

- The reranker sees only the **top-N retrieved candidates**, the same window a live
  search would pay for. A relevant item outside that window is reported separately
  as **unreachable**: no reranker can fix a recall miss.
- The baseline and the reranked ranking are scored with the same metric on the same
  queries, so the delta is attributable.
- Latency and model cost per query are reported next to the quality delta, because
  a reranker that buys +0.01 nDCG for a call per search is not obviously worth it.

Run::

    uv run python evals/esci_rerank.py -n 50            # probe
    uv run python evals/esci_rerank.py -n 500 --write   # full run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "discovery-rerank.md"
RESULTS = ROOT / "evals" / "results-esci-rerank.json"


def _gains(case: dict) -> dict[str, float]:
    from evals.esci_bench import GAINS

    return {c["product_id"]: GAINS.get(c["label"], 0.0) for c in case["candidates"]}


async def run(config: str, n: int, window: int, rebuild: bool, shards: int) -> dict:
    from app.adapters.cost_meter import UsageCostMeter
    from app.adapters.deepseek_client import DeepSeekClient
    from app.adapters.rerank_llm import LlmListwiseReranker
    from app.core.settings import load_settings
    from app.core.types import Chunk
    from app.evaluation.retrieval_metrics import evaluate_graded
    from evals.esci_bench import K, _embedding, _retriever, load_cases
    from evals.retriever_configs import parse_config

    settings = load_settings()
    cases = load_cases(n, rebuild, shards)
    embedding = _embedding(parse_config(config)[0])
    retriever = _retriever(config, embedding)
    meter = UsageCostMeter(settings.budget)
    # The meter carries all historical spend, so per-run cost is the DELTA.
    spent_before = meter.spent_cny()
    reranker = LlmListwiseReranker(
        DeepSeekClient(settings.llm),
        top_k=K,
        max_candidates=window,
        cost_meter=meter,
    )

    baseline_pairs: list[tuple[list[float], list[float]]] = []
    reranked_pairs: list[tuple[list[float], list[float]]] = []
    unreachable = 0
    latencies: list[float] = []

    for index, case in enumerate(cases, 1):
        retriever.add(
            [
                Chunk(id=c["product_id"], text=c["text"], source=c["product_id"])
                for c in case["candidates"]
            ]
        )
        gains = _gains(case)
        ranked = retriever.retrieve(case["query"], window)
        ranked_ids = [chunk.id for chunk in ranked]

        achievable = {pid for pid, gain in gains.items() if gain >= 0.1}  # E or S
        if achievable and not (achievable & set(ranked_ids)):
            unreachable += 1

        baseline_pairs.append(([gains.get(pid, 0.0) for pid in ranked_ids], list(gains.values())))

        started = time.perf_counter()
        reranked = await reranker.rerank(case["query"], ranked, K)
        latencies.append((time.perf_counter() - started) * 1000)
        reranked_pairs.append(
            ([gains.get(chunk.id, 0.0) for chunk in reranked], list(gains.values()))
        )
        if index % 10 == 0 or index == len(cases):
            print(f"  [{index}/{len(cases)}] cost=¥{meter.spent_cny():.4f}", flush=True)

    baseline = evaluate_graded(baseline_pairs, K)
    reranked = evaluate_graded(reranked_pairs, K)
    return {
        "config": config,
        "cases": len(cases),
        "window": window,
        "k": K,
        "baseline": {"ndcg": baseline.ndcg, "hit_rate": baseline.hit_rate, "mrr": baseline.mrr},
        "reranked": {"ndcg": reranked.ndcg, "hit_rate": reranked.hit_rate, "mrr": reranked.mrr},
        "unreachable": unreachable,
        "unreachable_share": round(unreachable / len(cases), 4) if cases else 0.0,
        "avg_rerank_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
        "cost_cny": round(meter.spent_cny() - spent_before, 6),
        "spent_before_cny": round(spent_before, 6),
        "model": settings.llm.model,
    }


def _report(result: dict) -> str:
    base, rer = result["baseline"], result["reranked"]
    delta = rer["ndcg"] - base["ndcg"]
    per_search = result["cost_cny"] / max(1, result["cases"])
    # A second stage that costs seconds per search needs a quality reason, not just a
    # positive delta: state both and let the reader see the trade.
    latency_bound = result["avg_rerank_ms"] > 2000
    lines = [
        "# Discovery: second-stage reranking (feature 046, step A6)",
        "",
        f"- Retriever: `{result['config']}`, reranker: **LLM listwise** "
        f"(`{result['model']}`), window **top-{result['window']}**, K={result['k']}.",
        f"- ESCI cases: **{result['cases']}** (500-query set sampled).",
        "",
        "| | nDCG@10 | hit@10 | MRR |",
        "| --- | ---: | ---: | ---: |",
        f"| retrieval only | {base['ndcg']:.4f} | {base['hit_rate']:.4f} | {base['mrr']:.4f} |",
        f"| + LLM listwise rerank | {rer['ndcg']:.4f} | {rer['hit_rate']:.4f} | {rer['mrr']:.4f} |",
        f"| **Δ** | **{delta:+.4f}** | {rer['hit_rate'] - base['hit_rate']:+.4f} | "
        f"{rer['mrr'] - base['mrr']:+.4f} |",
        "",
        f"- Cost: **¥{result['cost_cny']:.4f}** for {result['cases']} queries "
        f"(≈ ¥{per_search:.5f} per search; the meter's cumulative total is "
        f"{result['spent_before_cny']:.2f} + this run).",
        f"- Latency: **{result['avg_rerank_ms']:.0f} ms** added per search.",
        f"- **Unreachable**: {result['unreachable']}/{result['cases']} queries "
        f"({result['unreachable_share']:.1%}) have a relevant item outside the "
        f"top-{result['window']} window, which no reranker can recover.",
        "",
        "## Verdict",
        "",
    ]
    if delta > 0.005:
        lines.append(
            f"- Reranking **improves** ESCI nDCG@10 by {delta:+.4f} "
            f"(MRR {rer['mrr'] - base['mrr']:+.4f}) for ¥{per_search:.5f} and "
            f"{result['avg_rerank_ms']:.0f} ms per search."
        )
        if latency_bound:
            lines.append(
                f"- **But {result['avg_rerank_ms'] / 1000:.1f} s per search disqualifies it as an "
                "inline step in a live search**: the quality gain only pays off where latency is "
                "not on the user's path (offline ranking, a batch re-rank, or an async "
                "'refining results' affordance)."
            )
        else:
            lines.append(
                "- The latency is small enough that the quality gain is a fair trade for a live "
                "search path."
            )
    elif delta < -0.005:
        lines.append(
            f"- Reranking **hurts** ({delta:+.4f}): the listwise model reorders worse "
            "than first-stage retrieval on this corpus, so it must stay off."
        )
    else:
        lines.append(
            f"- Reranking is **neutral** ({delta:+.4f}) at "
            f"¥{result['cost_cny'] / max(1, result['cases']):.5f} and "
            f"{result['avg_rerank_ms']:.0f} ms per search, so it is not worth shipping: "
            "a second stage that costs a call per query must buy ranking quality."
        )
    lines += [
        "",
        "The unreachable share is the ceiling: if a relevant item never entered the "
        "window, only better first-stage retrieval (recall) can surface it.",
        "",
    ]
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=50)
    parser.add_argument("--config", default="tfidf")
    parser.add_argument("--window", type=int, default=20, help="candidates sent to the reranker")
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    result = await run(args.config, args.n, args.window, args.rebuild, args.shards)
    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    text = _report(result)
    print(text)
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(text)
        print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
