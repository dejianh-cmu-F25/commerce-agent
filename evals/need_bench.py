#!/usr/bin/env python3
"""Need-based discovery: does retrieval over product text beat a keyword index? (047)

Runs ``evals/need_cases.jsonl`` (need/task queries whose matching words live in the
review or feature text, not the title) against the catalog retrievers and reports
hit@k / recall@k / MRR. The comparison is the point:

- **tfidf-plain** - a title/vendor/type/tag index: the "traditional keyword" baseline.
- **tfidf-enriched** - the same lexical retriever over the full document
  (features + cleaned review evidence). This is the cheapest "RAG" (retrieval over
  the unstructured product text).
- **dense-hash** - keyless dense (lexical feature hashing; not semantics).
- ``--real`` adds **dense-openai** and **hybrid-openai** (a real embedding), which
  is where semantics - not just extra words - is measured.

Keyless by default (no key, no network); ``--real`` uses the configured provider.

Run::

    uv run python evals/need_bench.py                 # keyless
    uv run python evals/need_bench.py --real --write   # real embedding + report
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "need_cases.jsonl"
SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
RESULTS = ROOT / "evals" / "results-need.json"
REPORT = ROOT / "reports" / "discovery-need.md"
K = 10

KEYLESS = ("tfidf-plain", "tfidf-enriched", "dense-hash")
REAL = ("dense-openai", "hybrid-openai")


def _load_cases() -> list[dict]:
    if not CASES.exists():
        return []
    return [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]


def _snapshot() -> list[dict]:
    return json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else []


def _evaluate(cases: list[dict], retrieve) -> dict:
    from app.evaluation.retrieval_metrics import evaluate_retrieval

    pairs: list[tuple[list[str], set[str]]] = []
    by_type: dict[str, list[tuple[list[str], set[str]]]] = {}
    latencies: list[float] = []
    for case in cases:
        start = time.perf_counter()
        ranked = retrieve(case["query"], K)
        latencies.append((time.perf_counter() - start) * 1000)
        pair = (ranked, set(case["expected_ids"]))
        pairs.append(pair)
        by_type.setdefault(case["need_type"], []).append(pair)
    metrics = evaluate_retrieval(pairs, K)
    return {
        "hit_rate": metrics.hit_rate,
        "recall": metrics.recall,
        "mrr": metrics.mrr,
        "avg_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "by_type": {
            kind: evaluate_retrieval(items, K).hit_rate for kind, items in sorted(by_type.items())
        },
    }


_BASE = {
    "tfidf-plain": "tfidf",
    "tfidf-enriched": "tfidf",
    "dense-hash": "dense-hash",
    "dense-openai": "dense-openai",
    "hybrid-openai": "hybrid-openai",
}


def _retriever(config: str, products: list[dict], reviews):
    """Build the retriever for a config; the doc set follows the ``-enriched`` suffix."""
    from evals.bench_discovery import _local_retriever

    if config not in _BASE:
        raise ValueError(f"unknown config: {config}")
    enriched = config.endswith("enriched")
    return _local_retriever(_BASE[config], products, reviews if enriched else None)


def run(configs: tuple[str, ...], write: bool) -> dict:
    cases = _load_cases()
    products = _snapshot()
    if not cases or not products:
        print("need cases or catalog snapshot missing; nothing to run (keyless gate stays green)")
        return {}
    reviews = None
    try:
        from evals.bench_discovery import _reviews

        reviews = _reviews()
    except Exception:  # noqa: BLE001 - no review store is a valid keyless state
        reviews = None

    result: dict = {"k": K, "cases": len(cases), "configs": {}}
    for config in configs:
        enriched = config.endswith("enriched")
        if enriched and reviews is None:
            print(f"  {config} skipped (no review store)")
            continue
        retriever = _retriever(config, products, reviews)
        result["configs"][config] = _evaluate(
            cases, lambda query, limit, r=retriever: [h.id for h in r.retrieve(query, limit)]
        )
        print(f"  {config} done", flush=True)

    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    print(f"need benchmark (k={K}, {result['cases']} cases)")
    for config, metrics in result["configs"].items():
        print(
            f"  {config:<16} hit@{K}={metrics['hit_rate']:.3f} "
            f"recall@{K}={metrics['recall']:.3f} mrr={metrics['mrr']:.3f} "
            f"avg={metrics['avg_ms']:.1f}ms"
        )
    if write:
        _write_report(result)
        print(f"wrote {REPORT}")
    return result


def _write_report(result: dict) -> None:
    from app.evaluation.report_meta import with_marker

    lines = [
        "# Product RAG: need-based discovery vs keyword search",
        "",
        'A **need query** names a task or situation, not a product ("something to keep',
        'dog hair off my clothes while grooming him"). The matching words live in the',
        "**review / feature text**, so a title-only keyword index cannot serve it - which",
        "is the gap measured here.",
        "",
        "| Config | hit@10 | recall@10 | MRR | avg ms |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for config, metrics in result["configs"].items():
        lines.append(
            f"| {config} | {metrics['hit_rate']:.3f} | {metrics['recall']:.3f} | "
            f"{metrics['mrr']:.3f} | {metrics['avg_ms']:.1f} |"
        )
    plain = result["configs"].get("tfidf-plain", {}).get("hit_rate")
    enriched = result["configs"].get("tfidf-enriched", {}).get("hit_rate")
    if plain is not None and enriched is not None:
        lines += [
            "",
            f"Reading: a title-only keyword index scores **{plain:.3f}** hit@10; retrieving",
            f"over the product text (features + reviews) already scores **{enriched:.3f}** - the",
            "capability a product RAG adds before any semantic embedding.",
        ]
    if result["configs"]:
        best_config, best = max(result["configs"].items(), key=lambda kv: kv[1]["hit_rate"])
        if plain is not None and best["hit_rate"] > plain:
            delta = best["hit_rate"] - plain
            ratio = best["hit_rate"] / plain if plain else 0.0
            lines += [
                "",
                f"**Headline** - the best config (`{best_config}`) reaches "
                f"**{best['hit_rate']:.3f}** hit@10 vs the keyword baseline's "
                f"**{plain:.3f}** (**{delta:+.3f}** absolute, **{ratio:.1f}×**): a real",
                "embedding, not just extra words in the index, is what serves need queries.",
            ]
    lines += [
        "",
        "## Method",
        "",
        "- Cases: `evals/need_cases.jsonl`; each label is provable - the product's own",
        "  text states it serves the need (`evals/need_cases.py` checks this).",
        "- Metrics via `app/evaluation/retrieval_metrics.py` (hit@k / recall@k / MRR).",
        "- `dense-hash` is keyless feature hashing (lexical), not semantics; run `--real`",
        "  for a real embedding.",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        with_marker(
            "\n".join(lines) + "\n",
            "evals/need_bench.py",
            result["cases"],
            ["evals/need_cases.jsonl", "data/discovery/products.json"],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", help="also run a real embedding")
    parser.add_argument("--write", action="store_true", help="write the report")
    args = parser.parse_args()
    configs = KEYLESS + (REAL if args.real else ())
    run(configs, args.write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
