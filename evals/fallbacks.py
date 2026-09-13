"""Keyless dependency-fallback coverage (feature 031, RD-1).

Exercises the declared fallbacks — a failing retriever, a missing knowledge dir,
a failing LLM — and scores how many dependencies degrade instead of crashing.
Writes the result to ``evals/results-keyless.json`` (regenerated, not committed).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Sequence
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.storefront_memory import InMemoryStorefront
from app.core import events as ev
from app.core.loop import Agent
from app.core.resilience import FallbackRetriever
from app.core.session import Session
from app.core.settings import AgentSettings
from app.core.types import Chunk, LLMEvent, Message, ToolSpec
from app.knowledge.ingest import load_chunks
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry
from evals.retrieval_set import RETRIEVAL_SET

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = str(ROOT / "config" / "knowledge")
RESULTS_PATH = ROOT / "evals" / "results-keyless.json"
MIN_COVERAGE = 1.0


class FailingRetriever:
    def __init__(self) -> None:
        self.attempts = 0

    def add(self, chunks: list[Chunk]) -> None:
        return None

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        self.attempts += 1
        raise RuntimeError("vector store unavailable")


class FailingLLM:
    async def stream(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec] = ()
    ) -> AsyncIterator[LLMEvent]:
        raise RuntimeError("provider unavailable")
        yield  # pragma: no cover - makes this an async generator


async def _retriever_fallback() -> bool:
    primary = FailingRetriever()
    secondary = InMemoryRetriever()
    secondary.add(load_chunks(KNOWLEDGE_DIR))
    wrapper = FallbackRetriever(primary, secondary)
    hits = wrapper.retrieve(RETRIEVAL_SET[0].query, 3)
    wrapper.retrieve("another query", 3)  # must not retry the dead primary
    return (
        bool(hits) and wrapper.degraded and len(wrapper.degradations) == 1 and primary.attempts == 1
    )


async def _retriever_healthy() -> bool:
    primary = InMemoryRetriever()
    primary.add(load_chunks(KNOWLEDGE_DIR))
    secondary = InMemoryRetriever()
    secondary.add(load_chunks(KNOWLEDGE_DIR))
    wrapper = FallbackRetriever(primary, secondary)
    hits = wrapper.retrieve(RETRIEVAL_SET[0].query, 3)
    return bool(hits) and not wrapper.degraded


async def _retriever_disabled() -> bool:
    secondary = InMemoryRetriever()
    secondary.add(load_chunks(KNOWLEDGE_DIR))
    wrapper = FallbackRetriever(FailingRetriever(), secondary, enabled=False)
    try:
        wrapper.retrieve("x", 3)
    except RuntimeError:
        return True
    return False


async def _knowledge_missing() -> bool:
    return load_chunks(str(ROOT / "does-not-exist")) == []


async def _llm_failure_surfaces() -> bool:
    registry = ToolRegistry()
    register_catalog_tools(registry, InMemoryStorefront(SEED_PRODUCTS))
    agent = Agent(
        llm=FailingLLM(),
        tools=registry,
        settings=AgentSettings(max_turns=3),
        system_prompt="You are a test assistant.",
    )
    sink = ListSink()
    await agent.stream_turn(Session(id="fallback"), "hello", sink)
    return bool(sink.of_type(ev.ErrorEvent)) and sink.of_type(ev.TurnEnd)[-1].reason == "error"


# (name, coroutine, needs the declared fallback wrapper)
CASES: list[tuple[str, object, bool]] = [
    ("retriever_fallback", _retriever_fallback, True),
    ("retriever_healthy", _retriever_healthy, True),
    ("retriever_disabled", _retriever_disabled, True),
    ("knowledge_missing", _knowledge_missing, False),
    ("llm_failure_surfaces", _llm_failure_surfaces, False),
]


async def run_fallbacks() -> dict:
    passed = 0
    baseline = 0
    failures: list[str] = []
    for name, case, needs_fallback in CASES:
        try:
            ok = bool(await case())  # type: ignore[operator]
        except Exception as exc:  # a crash is a failed case, not a failed run
            ok = False
            failures.append(f"{name}: raised {exc!r}")
        if ok:
            passed += 1
            if not needs_fallback:
                baseline += 1
        elif not any(f.startswith(name) for f in failures):
            failures.append(name)
    total = len(CASES)
    return {
        "cases": total,
        "passed": passed,
        "coverage": round(passed / total, 4) if total else 0.0,
        "baseline_passed": baseline,
        "baseline_coverage": round(baseline / total, 4) if total else 0.0,
        "failures": failures,
    }


def write_keyless(result: dict) -> None:
    data: dict = {}
    if RESULTS_PATH.exists():
        try:
            data = json.loads(RESULTS_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["fallbacks"] = result
    RESULTS_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    result = asyncio.run(run_fallbacks())
    print(f"dependency fallbacks ({result['cases']} cases)")
    print(f"  before (no fallback)={result['baseline_coverage']:.3f}")
    print(f"  after (declared)={result['coverage']:.3f}  ({result['passed']}/{result['cases']})")
    for failure in result["failures"]:
        print(f"  FAIL {failure}")
    write_keyless(result)
    if result["coverage"] < MIN_COVERAGE:
        print(f"FAIL: fallback coverage below {MIN_COVERAGE}")
        return 1
    print(f"OK: fallback coverage >= {MIN_COVERAGE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
