#!/usr/bin/env python3
"""ESCI retrieval benchmark (feature 046, discovery layer).

External, **human-labeled** relevance (Exact / Substitute / Complement /
Irrelevant) from Amazon's Shopping Queries Dataset (``tasksource/esci``,
Apache-2.0). Ranks the candidates ESCI provides for each query with the keyless
retrievers and reports **nDCG@10** (the ESCI metric).

Streams the dataset (no 2.5 GB download) and caches the built cases under
``data/esci/`` (gitignored).

Run::

    uv run python evals/esci_bench.py            # build/use cache, run
    uv run python evals/esci_bench.py --rebuild  # ignore the cache
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "esci"
CACHE = DATA / "cases.json"
RESULTS = ROOT / "evals" / "results-esci.json"
# ESCI grades -> gains (the Amazon KDD Cup 2022 mapping).
GAINS = {"Exact": 1.0, "Substitute": 0.1, "Complement": 0.01, "Irrelevant": 0.0}
K = 10
DIMS = 256
CONFIGS = ["tfidf", "dense-hash"]
BASE = "https://huggingface.co/datasets/tasksource/esci/resolve/main/data"
SHARDS = [
    "test-00000-of-00004-d48474212b95f33b.parquet",
    "test-00001-of-00004-b7602f1b5c136953.parquet",
    "test-00002-of-00004-a81cff173329b486.parquet",
    "test-00003-of-00004-22af4ca7fa1313b2.parquet",
]


def _download(shard: str) -> Path:
    """Download one parquet shard with visible progress (skips if present)."""
    import httpx

    dest = DATA / shard
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    DATA.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/{shard}"
    with httpx.stream("GET", url, timeout=180, follow_redirects=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        done = 0
        next_mark = 50 << 20
        with dest.open("wb") as handle:
            for chunk in response.iter_bytes(1 << 20):
                handle.write(chunk)
                done += len(chunk)
                if done >= next_mark:
                    print(f"    downloaded {done / 1e6:.0f}/{total / 1e6:.0f} MB", flush=True)
                    next_mark += 50 << 20
    return dest


def _rows(path: Path):
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=50000):
        yield from batch.to_pylist()


def _collect(groups: dict, row: dict) -> None:
    if row.get("product_locale") != "us":
        return
    query_id = row["query_id"]
    group = groups.get(query_id)
    if group is None:
        group = {"query_id": query_id, "query": row["query"], "candidates": []}
        groups[query_id] = group
    group["candidates"].append(
        {
            "product_id": row["product_id"],
            "text": row.get("product_text") or row.get("product_title") or "",
            "label": row["esci_label"],
        }
    )


def build_cases(n: int, shards: int = 1) -> list[dict]:
    groups: dict[int, dict] = {}
    for shard in SHARDS[:shards]:
        print(f"  shard {shard[:20]}…", flush=True)
        path = _download(shard)
        for row in _rows(path):
            _collect(groups, row)
        ready = [g for g in groups.values() if len(g["candidates"]) >= 2]
        print(f"    -> {len(groups)} queries, {len(ready)} usable", flush=True)
        if len(ready) >= n:
            break
    ready = [g for g in groups.values() if len(g["candidates"]) >= 2]
    import random

    if len(ready) > n:
        return random.Random(0).sample(ready, n)  # seeded: reproducible, unbiased slice
    return ready


def load_cases(n: int, rebuild: bool, shards: int) -> list[dict]:
    if CACHE.exists() and not rebuild:
        cached = json.loads(CACHE.read_text())
        if len(cached) >= n:
            print(f"using cache: {len(cached)} cases", flush=True)
            return cached[:n]
    cases = build_cases(n, shards)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cases))
    return cases


def _retriever(config: str):
    from app.adapters.embedding_hash import HashEmbeddingProvider
    from app.adapters.retriever_dense import DenseRetriever
    from app.adapters.retriever_memory import InMemoryRetriever
    from app.adapters.vector_memory import InMemoryVectorStore

    if config == "tfidf":
        return InMemoryRetriever()
    if config == "dense-hash":
        return DenseRetriever(HashEmbeddingProvider(DIMS), InMemoryVectorStore())
    raise ValueError(config)


def run(cases: list[dict]) -> dict:
    from app.core.types import Chunk
    from app.evaluation.retrieval_metrics import evaluate_graded

    result: dict = {"k": K, "cases": len(cases), "configs": {}}
    for config in CONFIGS:
        pairs: list[tuple[list[float], list[float]]] = []
        latencies: list[float] = []
        for case in cases:
            retriever = _retriever(config)
            retriever.add(
                [
                    Chunk(id=c["product_id"], text=c["text"], source=c["product_id"])
                    for c in case["candidates"]
                ]
            )
            start = time.perf_counter()
            ranked = [hit.id for hit in retriever.retrieve(case["query"], len(case["candidates"]))]
            latencies.append((time.perf_counter() - start) * 1000)
            gains = {c["product_id"]: GAINS.get(c["label"], 0.0) for c in case["candidates"]}
            pairs.append(([gains.get(pid, 0.0) for pid in ranked], list(gains.values())))
        metrics = evaluate_graded(pairs, K)
        result["configs"][config] = {
            "ndcg": metrics.ndcg,
            "hit_rate": metrics.hit_rate,
            "mrr": metrics.mrr,
            "avg_ms": round(sum(latencies) / len(latencies), 3),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=500)
    parser.add_argument("--shards", type=int, default=1, help="parquet shards to download (1..4)")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    cases = load_cases(args.n, args.rebuild, args.shards)
    if not cases:
        print("FAIL: no ESCI cases built")
        return 1
    result = run(cases)
    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    print(f"ESCI benchmark (k={K}, {result['cases']} queries, us locale)")
    for config, metrics in result["configs"].items():
        print(
            f"  {config:<11} nDCG@{K}={metrics['ndcg']:.3f}  hit@{K}={metrics['hit_rate']:.3f}  "
            f"mrr={metrics['mrr']:.3f}  avg={metrics['avg_ms']:.2f}ms"
        )
    print(f"wrote {RESULTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
