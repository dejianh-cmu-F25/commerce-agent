#!/usr/bin/env python3
"""Discovery benchmark over our catalog (feature 046, discovery layer).

Runs the rule-generated cases (``evals/discovery_cases.jsonl``) against the
catalog retrievers and reports hit@k / recall@k / MRR, overall and per rule.

Configs:
- ``tfidf`` — keyless lexical (the baseline)
- ``dense-hash`` — keyless dense (lexical hash embeddings)
- ``shopify-keyword`` — the **live** retriever (Shopify Admin ``products(query:)``),
  sampled because it is a network call

Run::

    uv run python evals/bench_discovery.py
    uv run python evals/bench_discovery.py --shopify-sample 50
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "discovery_cases.jsonl"
SNAPSHOT = ROOT / "data" / "discovery" / "products.json"
RESULTS = ROOT / "evals" / "results-discovery.json"
K = 10
DIMS = 256


def _load() -> tuple[list[dict], list[dict]]:
    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    products = json.loads(SNAPSHOT.read_text())
    return cases, products


def _document(product: dict) -> str:
    tags = [t for t in product["tags"] if not t.startswith("imported:")]
    return " ".join([product["title"], product["vendor"], product["type"], *tags]).strip()


def _embedding(config: str):
    from app.adapters.embedding_hash import HashEmbeddingProvider

    if config == "tfidf":
        return None
    if config == "dense-hash":
        return HashEmbeddingProvider(DIMS)
    if config in ("dense-openai", "hybrid-openai"):
        from app.adapters.embedding_cache import CachedEmbeddingProvider
        from app.adapters.embedding_openai import OpenAIEmbeddingProvider
        from app.core.settings import load_settings

        settings = load_settings()
        base = OpenAIEmbeddingProvider(
            model=settings.embedding.model,
            api_key=settings.embedding.api_key,
            base_url=settings.embedding.base_url,
        )
        return CachedEmbeddingProvider(base, ROOT / "data" / "embeddings.sqlite")
    raise ValueError(config)


def _local_retriever(config: str, products: list[dict]):
    from app.adapters.retriever_dense import DenseRetriever
    from app.adapters.retriever_hybrid import HybridRetriever
    from app.adapters.retriever_memory import InMemoryRetriever
    from app.adapters.vector_memory import InMemoryVectorStore
    from app.core.types import Chunk
    from evals.retriever_configs import parse_config

    kind, weights = parse_config(config)
    if kind == "tfidf":
        retriever = InMemoryRetriever()
    else:
        embedding = _embedding(kind)
        assert embedding is not None
        dense = DenseRetriever(embedding, InMemoryVectorStore())
        if kind.startswith("hybrid"):
            retriever = HybridRetriever(InMemoryRetriever(), dense, weights=weights or (1.0, 1.0))
        else:
            retriever = dense
    retriever.add([Chunk(id=p["id"], text=_document(p), source=p["id"]) for p in products])
    return retriever


def _shopify_search(query: str, limit: int) -> list[str]:
    import os

    from app.adapters.shopify_catalog import ShopifyCatalog
    from app.core.settings import load_settings

    if os.environ.get("SHOPIFY_SHOP") is None:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"'))
    settings = load_settings()
    catalog = ShopifyCatalog(
        settings.shopify.shop, settings.shopify.access_token, settings.shopify.api_version
    )
    return [product.id for product in catalog.search(query, limit)]


def _evaluate(cases: list[dict], retrieve) -> dict:
    from app.evaluation.retrieval_metrics import evaluate_retrieval

    latencies: list[float] = []
    by_rule: dict[str, list[tuple[list[str], set[str]]]] = {}
    pairs: list[tuple[list[str], set[str]]] = []
    for case in cases:
        start = time.perf_counter()
        ranked = retrieve(case["query"], K)
        latencies.append((time.perf_counter() - start) * 1000)
        pair = (ranked, set(case["expected_ids"]))
        pairs.append(pair)
        by_rule.setdefault(case["rule"], []).append(pair)
    metrics = evaluate_retrieval(pairs, K)
    return {
        "hit_rate": metrics.hit_rate,
        "recall": metrics.recall,
        "mrr": metrics.mrr,
        "avg_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "by_rule": {
            rule: evaluate_retrieval(items, K).hit_rate for rule, items in sorted(by_rule.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shopify-sample", type=int, default=0, help="cases for the live retriever"
    )
    args = parser.parse_args()

    cases, products = _load()
    result: dict = {"k": K, "cases": len(cases), "configs": {}}
    for config in ("tfidf", "dense-openai", "hybrid-openai"):
        retriever = _local_retriever(config, products)
        result["configs"][config] = _evaluate(
            cases, lambda query, limit, r=retriever: [h.id for h in r.retrieve(query, limit)]
        )
        print(f"  {config} done", flush=True)

    if args.shopify_sample:
        sample = cases[: args.shopify_sample]
        result["configs"]["shopify-keyword"] = _evaluate(sample, _shopify_search)
        result["shopify_sample"] = len(sample)
        print(f"  shopify-keyword done ({len(sample)} sampled)", flush=True)

    RESULTS.write_text(json.dumps(result, indent=2) + "\n")
    print(f"discovery benchmark (k={K}, {result['cases']} cases)")
    for config, metrics in result["configs"].items():
        print(
            f"  {config:<16} hit@{K}={metrics['hit_rate']:.3f} "
            f"recall@{K}={metrics['recall']:.3f} mrr={metrics['mrr']:.3f} "
            f"avg={metrics['avg_ms']:.1f}ms"
        )
        print(f"    by rule: {metrics['by_rule']}")
    print(f"wrote {RESULTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
