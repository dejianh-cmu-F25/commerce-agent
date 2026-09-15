#!/usr/bin/env python3
"""Plain vs enriched documents on the attribute queries (feature 046, step B/D/E).

The rule set says enrichment *hurts* (tfidf hit@10 0.991 -> 0.954): it adds vocabulary
a keyword query never asked for. The attribute set is the query class enrichment is
for - "Amazon Fashion runs small", where the phrase exists only in review text - so
this measures the pair on the queries that motivated the work.

Both document modes are indexed from the same 3,000-product snapshot, so the only
variable is whether the document carries features and review evidence.

Run::

    uv run python evals/bench_attribute.py            # report
    uv run python evals/bench_attribute.py --write    # also write the report
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.evaluation.report_meta import with_marker

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "attribute_cases.jsonl"
REPORT = ROOT / "reports" / "discovery-attribute.md"
RESULTS = ROOT / "evals" / "results-attribute.json"
K = 10


def _evaluate(config: str, cases: list[dict], products: list[dict], reviews) -> dict:
    from app.evaluation.retrieval_metrics import evaluate_retrieval
    from evals.bench_discovery import _local_retriever

    retriever = _local_retriever(config, products, reviews)
    pairs: list[tuple[list[str], set[str]]] = []
    latencies: list[float] = []
    for case in cases:
        started = time.perf_counter()
        hits = retriever.retrieve(case["query"], K)
        latencies.append((time.perf_counter() - started) * 1000)
        pairs.append(([hit.id for hit in hits], set(case["expected_ids"])))
    metrics = evaluate_retrieval(pairs, K)
    return {
        "hit_rate": metrics.hit_rate,
        "recall": metrics.recall,
        "mrr": metrics.mrr,
        "avg_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    from evals.bench_discovery import _load, _reviews

    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    _, products = _load()  # _load() -> (cases, products)
    reviews = _reviews()
    if reviews is None:
        print("FAIL: attribute cases need data/reviews/reviews.sqlite")
        return 1

    result: dict = {"k": K, "cases": len(cases), "configs": {}}
    for config in ("tfidf", "bm25", "hybrid-openai"):
        result["configs"][config] = {
            "plain": _evaluate(config, cases, products, None),
            "enriched": _evaluate(config, cases, products, reviews),
        }
        print(f"  {config} done", flush=True)

    lines = [
        "# Discovery: what review enrichment buys (feature 046, steps C/D/E)",
        "",
        f"- Attribute queries: **{len(cases)}**, each labelled by the review text that",
        "  contains the attribute (evals/attribute_cases.py) - no human judgement.",
        f"- Same 3,000-product snapshot in both modes; K={K}.",
        "",
        "| Config | documents | hit@10 | recall@10 | MRR | avg |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for config, modes in result["configs"].items():
        for mode in ("plain", "enriched"):
            m = modes[mode]
            lines.append(
                f"| `{config}` | {mode} | {m['hit_rate']:.3f} | {m['recall']:.3f} | "
                f"{m['mrr']:.3f} | {m['avg_ms']:.1f} ms |"
            )
    lines += ["", "## What this says", ""]
    for config, modes in result["configs"].items():
        delta = modes["enriched"]["hit_rate"] - modes["plain"]["hit_rate"]
        lines.append(
            f"- `{config}`: hit@10 {modes['plain']['hit_rate']:.3f} -> "
            f"{modes['enriched']['hit_rate']:.3f} (**{delta:+.3f}**) on attribute queries."
        )
    lines += [
        "",
        "Read this together with the rule set, where the same enrichment costs "
        "hit@10 0.991 -> 0.954. Enrichment is not a general improvement: it trades "
        "lexical precision for attribute recall, which is why the shipped document "
        "stays plain until a deployment knows its query mix (or keeps two indexes).",
        "",
    ]
    text = "\n".join(lines)
    print(text)
    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            with_marker(
                text,
                "evals/bench_attribute.py --write",
                len(cases),
                [CASES, "evals/bench_attribute.py"],
            )
        )
        print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
