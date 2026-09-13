"""Keyless scale-envelope & SLO benchmark (feature 029, SC-1/SC-3).

Measures the keyless stack — TF-IDF retrieval and a full scripted agent turn — at
increasing concurrency, reports latency percentiles and throughput, and fails the
gate when a declared SLO budget is breached. Keyless and deterministic (P8).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.storefront_memory import InMemoryStorefront
from app.core.loop import Agent
from app.core.session import Session, derive_messages
from app.core.settings import AgentSettings, SafetySettings
from app.core.types import Chunk
from app.knowledge.ingest import load_chunks
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry
from evals.retrieval_set import RETRIEVAL_SET

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = str(ROOT / "config" / "knowledge")
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"

LEVELS = (1, 4, 16, 64)
TARGET_CONCURRENCY = 16
OPS_PER_LEVEL = 64
LARGE_CORPUS_CHUNKS = 10_000
LONG_SESSION_TURNS = 100

# Declared budgets (SC-3); see docs/scale.md. Generous regression guards: the
# measured p95 is tens of microseconds, so these catch an order-of-magnitude
# regression (e.g. an accidental network call or sleep) without flaking on a
# loaded host.
SLO = {
    "retrieval_p95_us": 2000.0,
    "turn_p95_us": 10000.0,
    "error_rate": 0.0,
    "large_corpus_p95_us": 50_000.0,
    "long_session_ms": 5_000.0,
}


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((p / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def _retrieval_op() -> Callable[[], Awaitable[None]]:
    retriever = InMemoryRetriever()
    retriever.add(load_chunks(KNOWLEDGE_DIR))
    queries = [case.query for case in RETRIEVAL_SET]
    counter = {"i": 0}

    async def op() -> None:
        query = queries[counter["i"] % len(queries)]
        counter["i"] += 1
        retriever.retrieve(query, 3)

    return op


def _turn_op() -> Callable[[], Awaitable[None]]:
    async def op() -> None:
        registry = ToolRegistry()
        register_catalog_tools(registry, InMemoryStorefront(SEED_PRODUCTS))
        agent = Agent(
            llm=MockLLMClient([text_turn("Here is a tent.")]),
            tools=registry,
            settings=AgentSettings(max_turns=6),
            system_prompt="You are a test assistant.",
            safety=SafetySettings(),
        )
        await agent.stream_turn(Session(id="scale"), "I need a tent", ListSink())

    return op


async def _measure(op: Callable[[], Awaitable[None]], concurrency: int, total: int) -> dict:
    latencies: list[float] = []
    errors = 0
    semaphore = asyncio.Semaphore(concurrency)

    async def one() -> None:
        nonlocal errors
        async with semaphore:
            start = time.perf_counter()
            try:
                await op()
            except Exception:  # counted, never hidden
                errors += 1
            latencies.append((time.perf_counter() - start) * 1_000_000.0)

    started = time.perf_counter()
    await asyncio.gather(*(one() for _ in range(total)))
    elapsed = time.perf_counter() - started
    return {
        "concurrency": concurrency,
        "ops": total,
        "errors": errors,
        "error_rate": round(errors / total, 4),
        "p50_us": round(_pct(latencies, 50), 1),
        "p95_us": round(_pct(latencies, 95), 1),
        "throughput_ops_s": round(total / elapsed, 1) if elapsed > 0 else 0.0,
    }


def _synthetic_chunks(count: int) -> list[Chunk]:
    """A deterministic, representative corpus of ``count`` chunks (SC-1 volume)."""
    base = load_chunks(KNOWLEDGE_DIR)
    return [
        Chunk(
            id=f"syn-{i}",
            text=f"{base[i % len(base)].text} (variant {i})",
            source=base[i % len(base)].source,
        )
        for i in range(count)
    ]


async def _large_corpus_retrieval() -> dict:
    retriever = InMemoryRetriever()
    retriever.add(_synthetic_chunks(LARGE_CORPUS_CHUNKS))
    queries = [case.query for case in RETRIEVAL_SET]
    counter = {"i": 0}

    async def op() -> None:
        query = queries[counter["i"] % len(queries)]
        counter["i"] += 1
        retriever.retrieve(query, 3)

    return await _measure(op, TARGET_CONCURRENCY, OPS_PER_LEVEL)


async def _long_session() -> dict:
    registry = ToolRegistry()
    register_catalog_tools(registry, InMemoryStorefront(SEED_PRODUCTS))
    agent = Agent(
        llm=MockLLMClient([text_turn("Here is a tent.")]),
        tools=registry,
        settings=AgentSettings(max_turns=6),
        system_prompt="You are a test assistant.",
        safety=SafetySettings(),
    )
    session = Session(id="long-session")
    sink = ListSink()
    started = time.perf_counter()
    for _ in range(LONG_SESSION_TURNS):
        await agent.stream_turn(session, "I need a tent", sink)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    messages = derive_messages(session, "You are a test assistant.")  # SL-1
    return {
        "turns": LONG_SESSION_TURNS,
        "elapsed_ms": round(elapsed_ms, 2),
        "events": len(session.events),
        "reconstructable": len(messages) >= 1,
    }


async def run_scale() -> dict:
    result: dict = {
        "levels": [],
        "slo": SLO,
        "envelope": {
            "catalog_products": len(SEED_PRODUCTS),
            "knowledge_chunks": len(load_chunks(KNOWLEDGE_DIR)),
            "concurrency_tested": list(LEVELS),
            "ops_per_level": OPS_PER_LEVEL,
            "target_concurrency": TARGET_CONCURRENCY,
            "large_corpus_chunks": LARGE_CORPUS_CHUNKS,
            "long_session_turns": LONG_SESSION_TURNS,
        },
    }
    for level in LEVELS:
        result["levels"].append(
            {
                "concurrency": level,
                "retrieval": await _measure(_retrieval_op(), level, OPS_PER_LEVEL),
                "turn": await _measure(_turn_op(), level, OPS_PER_LEVEL),
            }
        )
    result["large_corpus"] = await _large_corpus_retrieval()
    result["long_session"] = await _long_session()
    return result


def evaluate_slo(result: dict) -> list[str]:
    """Return the SLO breaches at the target concurrency (empty == pass)."""
    target = result["envelope"]["target_concurrency"]
    level = next((item for item in result["levels"] if item["concurrency"] == target), None)
    if level is None:
        return [f"no measurement at the target concurrency {target}"]
    failures: list[str] = []
    if level["retrieval"]["p95_us"] > SLO["retrieval_p95_us"]:
        failures.append(
            f"retrieval p95 {level['retrieval']['p95_us']}us > {SLO['retrieval_p95_us']}us"
        )
    if level["turn"]["p95_us"] > SLO["turn_p95_us"]:
        failures.append(f"turn p95 {level['turn']['p95_us']}us > {SLO['turn_p95_us']}us")
    if level["turn"]["error_rate"] > SLO["error_rate"]:
        failures.append(f"error rate {level['turn']['error_rate']} > {SLO['error_rate']}")

    large_corpus = result.get("large_corpus", {})
    if large_corpus and large_corpus.get("p95_us", 0.0) > SLO["large_corpus_p95_us"]:
        failures.append(
            f"large-corpus p95 {large_corpus['p95_us']}us > {SLO['large_corpus_p95_us']}us"
        )
    long_session = result.get("long_session", {})
    if long_session and long_session.get("elapsed_ms", 0.0) > SLO["long_session_ms"]:
        failures.append(f"long-session {long_session['elapsed_ms']}ms > {SLO['long_session_ms']}ms")
    if long_session and not long_session.get("reconstructable"):
        failures.append("long-session log is not reconstructable (SL-1)")
    return failures


def write_keyless(result: dict) -> None:
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["scale"] = result
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    result = asyncio.run(run_scale())
    envelope = result["envelope"]
    print(
        f"scale envelope (catalog={envelope['catalog_products']} "
        f"chunks={envelope['knowledge_chunks']} ops/level={envelope['ops_per_level']})"
    )
    for level in result["levels"]:
        retrieval, turn = level["retrieval"], level["turn"]
        print(
            f"  c={level['concurrency']:<3} "
            f"retrieval p50/p95={retrieval['p50_us']:.1f}/{retrieval['p95_us']:.1f}us  "
            f"turn p50/p95={turn['p50_us']:.1f}/{turn['p95_us']:.1f}us  "
            f"throughput={turn['throughput_ops_s']:.0f}ops/s  errors={turn['errors']}"
        )
    large_corpus = result["large_corpus"]
    long_session = result["long_session"]
    print(
        f"  large corpus ({envelope['large_corpus_chunks']} chunks, c={TARGET_CONCURRENCY}): "
        f"p50/p95={large_corpus['p50_us']:.1f}/{large_corpus['p95_us']:.1f}us"
    )
    print(
        f"  long session ({long_session['turns']} turns): {long_session['elapsed_ms']:.1f}ms, "
        f"{long_session['events']} events, reconstructable={long_session['reconstructable']}"
    )
    write_keyless(result)
    failures = evaluate_slo(result)
    if failures:
        for failure in failures:
            print(f"FAIL: SLO breach at concurrency {TARGET_CONCURRENCY}: {failure}")
        return 1
    print(f"OK: SLOs met at concurrency {TARGET_CONCURRENCY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
