"""Keyless retrieval benchmark and ablation (feature 022).

Evaluates the same labeled query set with three retriever configs and writes the
results to ``evals/results-keyless.json`` (regenerated, not committed). The gate
runs this and fails if any config's hit-rate falls below the threshold.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from app.adapters.embedding_hash import HashEmbeddingProvider
from app.adapters.retriever_dense import DenseRetriever
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.vector_chroma import ChromaVectorStore
from app.adapters.vector_memory import InMemoryVectorStore
from app.evaluation.retrieval_metrics import evaluate_retrieval
from app.knowledge.ingest import load_chunks
from app.ports.retriever import Retriever
from evals.retrieval_set import RETRIEVAL_SET

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = str(ROOT / "config" / "knowledge")
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"
K = 3
MIN_HIT_RATE = 0.7
EMBEDDING_DIMS = 256
CONFIGS = ["tfidf", "dense-hash", "dense-chroma"]


def _build(config: str, tmp_dir: str) -> Retriever:
    chunks = load_chunks(KNOWLEDGE_DIR)
    retriever: Retriever
    if config == "tfidf":
        retriever = InMemoryRetriever()
    elif config == "dense-hash":
        retriever = DenseRetriever(HashEmbeddingProvider(EMBEDDING_DIMS), InMemoryVectorStore())
    elif config == "dense-chroma":
        retriever = DenseRetriever(
            HashEmbeddingProvider(EMBEDDING_DIMS),
            ChromaVectorStore(tmp_dir, "knowledge-bench"),
        )
    else:
        raise ValueError(f"unknown config: {config}")
    retriever.add(chunks)
    return retriever


def run_bench() -> dict:
    result: dict = {"k": K, "cases": len(RETRIEVAL_SET), "configs": {}}
    difficulties = sorted({case.difficulty for case in RETRIEVAL_SET})
    with tempfile.TemporaryDirectory() as tmp_dir:
        for config in CONFIGS:
            retriever = _build(config, tmp_dir)
            pairs: list[tuple[list[str], set[str]]] = []
            by_difficulty: dict[str, list[tuple[list[str], set[str]]]] = {
                level: [] for level in difficulties
            }
            latencies: list[float] = []
            for case in RETRIEVAL_SET:
                start = time.perf_counter()
                hits = retriever.retrieve(case.query, K)
                latencies.append((time.perf_counter() - start) * 1000)
                pair = ([hit.source for hit in hits], {case.expected_source})
                pairs.append(pair)
                by_difficulty[case.difficulty].append(pair)
            metrics = evaluate_retrieval(pairs, K)
            result["configs"][config] = {
                "hit_rate": metrics.hit_rate,
                "recall": metrics.recall,
                "mrr": metrics.mrr,
                "avg_ms": round(sum(latencies) / len(latencies), 3),
                "by_difficulty": {
                    level: evaluate_retrieval(items, K).hit_rate
                    for level, items in by_difficulty.items()
                },
            }
    return result


def write_keyless(result: dict) -> None:
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["retrieval"] = result
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    result = run_bench()
    width = max(len(config) for config in CONFIGS)
    print(f"retrieval benchmark (k={K}, {len(RETRIEVAL_SET)} queries)")
    for config, metrics in result["configs"].items():
        print(
            f"  {config:<{width}}  hit@{K}={metrics['hit_rate']:.3f}  "
            f"recall@{K}={metrics['recall']:.3f}  mrr={metrics['mrr']:.3f}  "
            f"avg={metrics['avg_ms']:.1f}ms"
        )
    write_keyless(result)
    failing = [c for c, m in result["configs"].items() if m["hit_rate"] < MIN_HIT_RATE]
    if failing:
        print(f"FAIL: hit-rate@{K} below {MIN_HIT_RATE}: {failing}")
        return 1
    print(f"OK: all configs hit-rate@{K} >= {MIN_HIT_RATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
