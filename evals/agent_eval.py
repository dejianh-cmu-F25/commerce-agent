"""Opt-in real-model evaluation (feature 023, book ch.7).

Runs the real agent (DeepSeek) over outcome-based cases × seeds and computes
reliability (Pass@1 / Pass@k / Best@k / Pass^k), process metrics, failure
attribution, and an optional rubric judge. Budget-capped (HR-12). Writes
``evals/results-real.json`` (not committed).

Usage:
    uv run python evals/agent_eval.py --real [--seeds 3] [--no-judge]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.cost_meter import UsageCostMeter
from app.adapters.deepseek_client import DeepSeekClient
from app.adapters.memory_memory import InMemoryMemoryStore
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.tracer_jsonl import JsonlTracer
from app.core import events as ev
from app.core.loop import Agent
from app.core.prompts import load_prompt
from app.core.session import AssistantMessage, Session, ToolResultEvent
from app.core.settings import Settings, load_settings
from app.evaluation.agent_metrics import RunMetrics, summarize
from app.evaluation.failure import attribute
from app.evaluation.reliability import aggregate
from app.evaluation.rubric import JudgeResult, judge_answer
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.knowledge import register_knowledge_tools
from app.tools.orders import register_order_tools
from app.tools.registry import ToolRegistry
from app.tools.skills import register_skill_tools
from evals.real_cases import CASE_NAMES, RealCase, build_cases
from web.main import build_retriever, build_skill_library

ROOT = Path(__file__).resolve().parents[1]
REAL_PATH = ROOT / "evals" / "results-real.json"
CUSTOMER = "eval-real"


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _build_agent(settings: Settings, llm: DeepSeekClient, tracer: JsonlTracer) -> tuple[Agent, str]:
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront)
    register_order_tools(registry, storefront, settings.returns.window_days)
    register_knowledge_tools(registry, build_retriever(settings))

    system_prompt = load_prompt("system")
    skills = build_skill_library(settings)
    if len(skills) > 0:
        register_skill_tools(registry, skills)
        system_prompt += "\n\n## Available skills\n" + skills.catalog()

    agent = Agent(
        llm=llm,
        tools=registry,
        settings=settings.agent,
        system_prompt=system_prompt,
        cost_meter=UsageCostMeter(settings.budget),
        tracer=tracer,
        memory=InMemoryMemoryStore(),
    )
    return agent, system_prompt


def _final_text(session: Session) -> str:
    for event in reversed(session.events):
        if isinstance(event, AssistantMessage) and event.text:
            return event.text
    return ""


def _tool_context(session: Session) -> str:
    return "\n".join(
        event.content for event in session.events if isinstance(event, ToolResultEvent)
    )


def _rendered_prices(sink: ListSink) -> list[float]:
    prices: list[float] = []
    for event in sink.of_type(ev.UIComponent):
        if event.component != "products":
            continue
        for item in (event.payload or {}).get("items", []):
            price = item.get("price") if isinstance(item, dict) else None
            if isinstance(price, (int, float)):
                prices.append(float(price))
    return prices


def _succeeds(case: RealCase, session: Session, sink: ListSink) -> bool:
    tools = {event.name for event in sink.of_type(ev.ToolCallStarted)}
    components = {event.component for event in sink.of_type(ev.UIComponent)}
    cart = {line.product_id for line in session.cart}
    answer = _final_text(session).lower()

    if case.max_price is not None and not any(
        price <= case.max_price for price in _rendered_prices(sink)
    ):
        return False
    if case.min_cart_items and len(session.cart) < case.min_cart_items:
        return False
    return (
        set(case.essential_tools) <= tools
        and set(case.essential_components) <= components
        and set(case.cart_contains) <= cart
        and all(needle.lower() in answer for needle in case.answer_contains)
        and not (set(case.forbidden_components) & components)
        and not (case.must_have_empty_cart and session.cart)
    )


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(0.95 * len(ordered)) - 1))
    return ordered[index]


def _summarize_runs(metrics: list[RunMetrics]) -> dict:
    if not metrics:
        return {}
    count = len(metrics)
    latencies = [item.latency_ms for item in metrics]
    return {
        "avg_steps": round(sum(item.steps for item in metrics) / count, 2),
        "tool_ok": sum(item.tool_ok for item in metrics),
        "tool_error": sum(item.tool_error for item in metrics),
        "ungrounded_attempts": sum(item.ungrounded_attempts for item in metrics),
        "avg_latency_ms": round(sum(latencies) / count, 1),
        "p95_latency_ms": round(_p95(latencies), 1),
        "prompt_tokens": sum(item.prompt_tokens for item in metrics),
        "completion_tokens": sum(item.completion_tokens for item in metrics),
        "cache_hit_tokens": sum(item.cache_hit_tokens for item in metrics),
        "cost_cny": round(sum(item.cost_cny for item in metrics), 6),
    }


def _summarize_judge(results: list[JudgeResult]) -> dict:
    if not results:
        return {}
    dimensions = [key for key in results[0].scores]
    avg = {
        dimension: round(
            sum(result.scores.get(dimension, 0) for result in results) / len(results), 2
        )
        for dimension in dimensions
    }
    return {
        "graded": len(results),
        "vetoes": sum(1 for result in results if result.veto),
        "avg_scores": avg,
    }


async def run_real(settings: Settings, seeds: int, use_judge: bool) -> dict:
    llm = DeepSeekClient(settings.llm)
    tracer = JsonlTracer(str(ROOT / "logs" / "eval-traces.jsonl"))
    agent, system_prompt = _build_agent(settings, llm, tracer)
    prompt_hash = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:12]
    meter = UsageCostMeter(settings.budget)
    start_cost = meter.spent_cny()
    cap = settings.evaluation.max_cost_cny

    outcomes: dict[str, list[bool]] = {name: [] for name in CASE_NAMES}
    run_metrics: list[RunMetrics] = []
    failure_counts: dict[str, int] = {}
    judge_results: list[JudgeResult] = []
    stopped = False

    for seed in range(seeds):
        for case in build_cases(seed):
            if meter.spent_cny() - start_cost >= cap:
                stopped = True
                break
            before = len(tracer.recent_spans(1_000_000))
            session = Session(id=f"eval-{case.name}-{seed}", customer_id=CUSTOMER)
            sink = ListSink()
            await agent.stream_turn(session, case.user_text, sink)
            spans = tracer.recent_spans(1_000_000)[before:]
            run_metrics.append(summarize(spans))

            success = _succeeds(case, session, sink)
            outcomes[case.name].append(success)
            if not success:
                attribution = attribute(session)
                # No tool error means the outcome predicate failed: incomplete.
                category = attribution.category if attribution else "incomplete"
                failure_counts[category] = failure_counts.get(category, 0) + 1

            if use_judge:
                judge_results.append(
                    await judge_answer(
                        llm,
                        question=case.user_text,
                        answer=_final_text(session),
                        context=_tool_context(session),
                        grounded_facts=[
                            event.content
                            for event in session.events
                            if isinstance(event, ToolResultEvent)
                        ],
                        model=settings.evaluation.judge_model,
                    )
                )
        if stopped:
            break

    reliability = aggregate([outcomes[name] for name in CASE_NAMES], settings.evaluation.pass_k)
    return {
        "model": settings.llm.model,
        "prompt_hash": prompt_hash,
        "judge_model": settings.evaluation.judge_model if use_judge else "disabled",
        "seeds": seeds,
        "pass_k": settings.evaluation.pass_k,
        "generated": datetime.now(UTC).date().isoformat(),
        "command": (
            f"uv run python evals/agent_eval.py --real --seeds {seeds}"
            + ("" if use_judge else " --no-judge")
        ),
        "stopped_at_cap": stopped,
        "reliability": {
            "runs": reliability.runs,
            "successes": reliability.successes,
            "tasks": reliability.tasks,
            "pass_at_1": reliability.pass_at_1,
            "pass_at_k": reliability.pass_at_k,
            "best_at_k": reliability.best_at_k,
            "pass_pow_k": reliability.pass_pow_k,
        },
        "process": _summarize_runs(run_metrics),
        "failures": failure_counts,
        "judge": _summarize_judge(judge_results),
        "per_task": {
            name: {
                "pass_at_1": round(sum(outcomes[name]) / len(outcomes[name]), 4),
                "pass_at_k": 1.0 if any(outcomes[name]) else 0.0,
                "pass_pow_k": (
                    1.0 if len(outcomes[name]) == seeds and all(outcomes[name]) else 0.0
                ),
            }
            for name in CASE_NAMES
        },
    }


def _write(agent_section: dict) -> None:
    data: dict = {}
    if REAL_PATH.exists():
        try:
            data = json.loads(REAL_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data["agent"] = agent_section
    REAL_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="run against the real model")
    parser.add_argument("--seeds", type=int, default=0, help="override evaluation.seeds")
    parser.add_argument("--no-judge", action="store_true", help="disable the rubric judge")
    args = parser.parse_args()

    _load_dotenv()
    settings = load_settings()
    if not args.real:
        print("This is the opt-in real-model runner; pass --real to run (it spends budget).")
        return 0
    if not settings.llm.api_key:
        print("FAIL: --real needs an API key (set LLM_API_KEY in .env).")
        return 1

    seeds = args.seeds or settings.evaluation.seeds
    use_judge = settings.evaluation.judge and not args.no_judge
    section = asyncio.run(run_real(settings, seeds, use_judge))
    _write(section)

    reliability = section["reliability"]
    print(
        f"real eval: model={section['model']} seeds={seeds} runs={reliability['runs']} "
        f"successes={reliability['successes']}"
    )
    print(
        f"  Pass@1={reliability['pass_at_1']:.3f}  Pass@k={reliability['pass_at_k']:.3f}  "
        f"Pass^k={reliability['pass_pow_k']:.3f}  "
        f"cost=CNY {section['process'].get('cost_cny', 0):.4f}"
    )
    if section["failures"]:
        print(f"  failures: {section['failures']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
