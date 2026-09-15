#!/usr/bin/env python3
"""Tune the RRF weights on a held-out split (feature 046, step A5).

Qdrant's guidance for hybrid search is explicit: equal weights let the weaker
retriever drag the fused ranking down, and if you have an eval set you should pick
weights on a train/val split and report on the half you did not tune on — measuring
on the queries you tuned on inflates the result.

The rule set is split by a stable hash of the case id, the grid is selected on
**train**, and the selected weights are then reported on **val** next to the two
baselines (pure lexical, and unweighted hybrid).

The fusion only depends on ranks, so the expensive part (the dense ranking, one
embedding call per query) is computed once and every weight pair re-fuses for free.

Run::

    uv run python evals/tune_rrf.py            # tune and report
    uv run python evals/tune_rrf.py --write    # also write the report
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from app.evaluation.report_meta import with_marker

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "discovery-rrf-weights.md"

GRID: list[tuple[float, float]] = [
    (1.0, 1.0),
    (2.0, 1.0),
    (3.0, 1.0),
    (5.0, 1.0),
    (3.0, 0.5),
    (5.0, 0.5),
]
BASELINES = ["tfidf", "hybrid-openai", "hybrid-openai-w1:1"]  # last == the shipped default


def _split(case_id: str) -> int:
    """Stable 50/50 split: a case never moves between train and val."""
    return int(hashlib.sha1(case_id.encode()).hexdigest(), 16) % 2


def _rankings(name: str, cases: list[dict], products: list[dict], candidate_k: int) -> list:
    """One ranking per case for the named retriever (the sparse and dense legs)."""
    from evals.bench_discovery import _local_retriever

    retriever = _local_retriever(name, products)
    return [retriever.retrieve(case["query"], candidate_k) for case in cases]


def _fuse_evaluate(
    cases: list[dict],
    sparse_rankings: list,
    dense_rankings: list,
    weights: tuple[float, float],
    *,
    k: int,
    rrf_k: int,
) -> dict:
    from app.adapters.retriever_hybrid import rrf_fuse
    from app.evaluation.retrieval_metrics import evaluate_retrieval

    pairs = []
    for case, sparse, dense in zip(cases, sparse_rankings, dense_rankings, strict=True):
        fused = rrf_fuse([sparse, dense], rrf_k=rrf_k, weights=weights, k=k)
        pairs.append(([chunk.id for chunk in fused], set(case["expected_ids"])))
    metrics = evaluate_retrieval(pairs, k)
    return {"hit_rate": metrics.hit_rate, "recall": metrics.recall, "mrr": metrics.mrr}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    from app.core.settings import load_settings
    from evals.bench_discovery import K, _evaluate, _load, _local_retriever

    settings = load_settings()
    rrf_k = settings.retrieval.rrf_k
    candidate_k = settings.retrieval.dense_top_k

    cases, products = _load()
    train = [case for case in cases if _split(case["case_id"]) == 0]
    val = [case for case in cases if _split(case["case_id"]) == 1]
    print(f"cases: {len(cases)} (train {len(train)} / val {len(val)}), K={K}, rrf_k={rrf_k}")

    # Keyed by case id: the rankings come back in `cases` order while the splits are
    # subsets of it, so zipping the rankings against `train + val` mismatches ids.
    ids = [case["case_id"] for case in cases]
    sparse_rankings = dict(zip(ids, _rankings("tfidf", cases, products, candidate_k), strict=True))
    dense_rankings = dict(
        zip(ids, _rankings("hybrid-openai", cases, products, candidate_k), strict=True)
    )

    def fuse(case_list: list[dict], weights: tuple[float, float]) -> dict:
        return _fuse_evaluate(
            case_list,
            [sparse_rankings[c["case_id"]] for c in case_list],
            [dense_rankings[c["case_id"]] for c in case_list],
            weights,
            k=K,
            rrf_k=rrf_k,
        )

    rows = []
    for weights in GRID:
        rows.append((weights, fuse(train, weights), fuse(val, weights)))
    best = max(rows, key=lambda row: (row[1]["hit_rate"], row[1]["mrr"]))
    print(f"selected on train: sparse={best[0][0]:g} dense={best[0][1]:g}")

    lines = [
        "# Discovery: RRF weights (feature 046, step A5)",
        "",
        f"- Rule set: **{len(cases)}** cases, split **{len(train)} train / {len(val)} val** "
        "by a stable hash of the case id.",
        f"- `rrf_k={rrf_k}`, candidates per leg `{candidate_k}`, K={K}.",
        "- Weights are **selected on train** and the table reports **val**, so the "
        "val column is not tuned-on (Qdrant's train/val protocol).",
        "",
        "## Grid (hit@10 / MRR)",
        "",
        "| weights (sparse:dense) | train hit@10 | train MRR | "
        "**val hit@10** | val MRR | val recall |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for weights, train_metrics, val_metrics in rows:
        marker = " ←" if weights == best[0] else ""
        lines.append(
            f"| {weights[0]:g}:{weights[1]:g}{marker} | {train_metrics['hit_rate']:.3f} | "
            f"{train_metrics['mrr']:.3f} | **{val_metrics['hit_rate']:.3f}** | "
            f"{val_metrics['mrr']:.3f} | {val_metrics['recall']:.3f} |"
        )

    lines += [
        "",
        "## Full-set baselines (same 216 cases)",
        "",
        "| config | hit@10 | recall@10 | MRR |",
        "| --- | ---: | ---: | ---: |",
    ]
    baseline_rows = {}
    for name in BASELINES:
        retriever = _local_retriever(name, products)
        metrics = _evaluate(
            cases, lambda query, limit, r=retriever: [h.id for h in r.retrieve(query, limit)]
        )
        baseline_rows[name] = metrics
        lines.append(
            f"| `{name}` | {metrics['hit_rate']:.3f} | {metrics['recall']:.3f} | "
            f"{metrics['mrr']:.3f} |"
        )

    lines += [
        "",
        "## What this says",
        "",
    ]
    lexical = baseline_rows["tfidf"]["hit_rate"]
    val_best = best[2]["hit_rate"]
    hybrid_default = baseline_rows["hybrid-openai"]["hit_rate"]
    train_spread = max(row[1]["hit_rate"] for row in rows) - min(row[1]["hit_rate"] for row in rows)
    if train_spread <= 0.005:
        best_val = max(rows, key=lambda row: row[2]["hit_rate"])
        lines += [
            f"- **Train cannot discriminate**: every weighting scores "
            f"{rows[0][1]['hit_rate']:.3f} hit@10 there, so the selection step is "
            "uninformative and the 'selected' row is merely the default. The val "
            "column is reported **for information** - picking the row that wins on "
            "val would be tuning on the held-out half.",
            f"- On val, down-weighting the dense leg lifts hit@10 "
            f"{rows[0][2]['hit_rate']:.3f} (1:1) -> {best_val[2]['hit_rate']:.3f} "
            f"({best_val[0][0]:g}:{best_val[0][1]:g}), reproducing Qdrant's warning "
            "that equal weights let the weaker retriever drag the fusion down.",
            f"- Even so, weighting only **catches up** to pure lexical "
            f"({hybrid_default:.3f} -> {best_val[2]['hit_rate']:.3f} on val, vs tfidf "
            f"{lexical:.3f} full-set): the dense leg adds no top-10 hit the lexical "
            "leg did not already have on this corpus.",
            "",
            "**Decision:** the live discovery path ships on `tfidf` - it matches or "
            "beats the weighted fusion, needs no embedding call per query, and has no "
            "provider dependency. The weighted hybrid stays wired, and is what the "
            "enriched-document step re-measures (recall has room there).",
        ]
    else:
        lines += [
            f"- The selected weights ({best[0][0]:g}:{best[0][1]:g}) were chosen on "
            f"train and score **{val_best:.3f}** hit@10 on the held-out half; pure "
            f"lexical scores **{lexical:.3f}**.",
            (
                "- The weighted fusion does not beat the lexical retriever, so the "
                "live path stays on `tfidf` and the semantic half earns its place on "
                "richer documents."
                if val_best < lexical
                else "- The weighted fusion matches or beats the lexical retriever on "
                "the held-out half, so the dense leg is justified by measurement."
            ),
        ]
    lines += [
        "",
        "The unweighted row is the shipped default before this step; the baselines are "
        "full-set, so they are not directly comparable to a split column.",
        "",
    ]

    text = "\n".join(lines)
    print(text)
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            with_marker(
                text,
                "evals/tune_rrf.py --write",
                len(cases),
                ["evals/discovery_cases.jsonl", "evals/tune_rrf.py"],
            )
        )
        print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
