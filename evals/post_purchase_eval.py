"""Two-layer post-purchase evaluation (feature 045).

Layer 1 (decision): per-case labels -> decision accuracy + policy-citation support.
Layer 2 (invariant): behavioral assertions -> invariant pass rate + no-fail rate.

Keyless mode is a deterministic self-test of the harness (no model). Real mode
runs the configured LLM (DeepSeek) against the same cases and is the evidence.

    uv run python evals/post_purchase_eval.py            # keyless self-test
    uv run python evals/post_purchase_eval.py --real      # real model (costs money)
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.adapters.cli_sink import ListSink
from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.core import events as ev
from app.core.loop import Agent
from app.core.prompts import load_prompt
from app.core.session import AssistantMessage, Session, ToolResultEvent
from app.core.settings import AgentSettings, load_settings
from app.evaluation.invariants import RunOutcome, evaluate
from app.gates.policy import PolicyGate
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem
from app.returns.amazon_policy import ReturnFacts, decide_return, load_amazon_policy
from app.tools.post_purchase import register_post_purchase_tools
from app.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]
DECISION_CASES = ROOT / "evals" / "post_purchase_cases.jsonl"
INVARIANT_CASES = ROOT / "evals" / "invariant_cases.jsonl"
POLICY_PATH = "config/policies/amazon.yaml"
RESULTS_PATH = ROOT / "evals" / "results-post-purchase.json"
EVAL_NOW = datetime(2026, 3, 1, tzinfo=UTC)
PROMPT = load_prompt("post_purchase")
POLICY = load_amazon_policy(POLICY_PATH)


@dataclass
class Outcome:
    reason: str = "stop"
    tool_calls: tuple[str, ...] = ()
    final_text: str = ""
    turns: int = 1
    error: bool = False
    proposal: dict[str, Any] | None = None

    def as_run_outcome(self, case: dict | None = None) -> RunOutcome:
        case = case or {}
        return RunOutcome(
            reason=self.reason,
            tool_calls=self.tool_calls,
            final_text=self.final_text,
            turns=self.turns,
            max_turns=8,
            error=self.error,
            system_prompt=PROMPT,
            proposal=self.proposal,
            expected_decision=str(case.get("expected_decision", "")),
            expected_clauses=tuple(case.get("expected_policy_refs", ())),
            allowed_ids=tuple(case.get("allowed_ids", ())),
            budget=case.get("budget"),
        )


@dataclass
class CaseResult:
    case_id: str
    ok: bool
    detail: str = ""
    failures: list[str] = field(default_factory=list)


def _load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _pad(case: dict) -> str:
    message = str(case.get("message", ""))
    target = case.get("pad_to_chars")
    if isinstance(target, int) and len(message) < target:
        message = message + " " + "x" * (target - len(message))
    return message


def _backend_for(case: dict) -> tuple[InMemoryPostPurchase, str]:
    """Build a one-order fixture; a foreign case has no order in the backend."""
    order_id = "1002" if case["case_id"] == "escalate-foreign-order" else f"order-{case['case_id']}"
    if case["case_id"] == "escalate-foreign-order":
        return InMemoryPostPurchase({}), order_id
    days = case.get("delivered_days_ago")
    delivered = (EVAL_NOW - timedelta(days=days)).isoformat() if days is not None else None
    line = LineItem(
        id=f"fli-{case['case_id']}",
        title="Item",
        quantity=1,
        sku="SKU",
        tags=tuple(case.get("item_tags", [])),
    )
    order = OrderView(
        id=order_id,
        name="#1001",
        created_at=(EVAL_NOW - timedelta(days=(days or 0) + 5)).isoformat(),
        financial_status="PAID",
        fulfillment_status=case.get("fulfillment_status", "FULFILLED"),
        total=100.0,
        currency="USD",
        delivered_at=delivered,
        line_items=[line],
    )
    return (
        InMemoryPostPurchase(
            {order_id: order}, {order_id: [ReturnableItem(line.id, "Item", "SKU", 1)]}
        ),
        order_id,
    )


def _build_agent(backend: InMemoryPostPurchase, llm, cost_meter=None) -> Agent:
    registry = ToolRegistry()
    # Mirror production (web/main.py): the policy gate is what attaches the
    # authoritative clause citations to a proposal.
    register_post_purchase_tools(
        registry, backend, policy_gate=PolicyGate(POLICY), now=EVAL_NOW
    )
    return Agent(
        llm=llm,
        tools=registry,
        settings=AgentSettings(max_turns=8),
        system_prompt=PROMPT,
        cost_meter=cost_meter,
    )


async def _run_case(case: dict, llm, *, with_order: bool, cost_meter=None) -> Outcome:
    backend, order_id = _backend_for(case) if with_order else (InMemoryPostPurchase({}), "")
    agent = _build_agent(backend, llm, cost_meter)
    message = _pad(case)
    if with_order and order_id:
        message = f"{message}\n\n(order id: {order_id})"
    session = Session(id=f"eval-{case['case_id']}")
    sink = ListSink()
    await agent.stream_turn(session, message, sink)

    tool_calls = tuple(event.name for event in sink.of_type(ev.ToolCallStarted))
    turns = len(sink.of_type(ev.ToolCallStarted)) + 1
    reason = sink.of_type(ev.TurnEnd)[-1].reason if sink.of_type(ev.TurnEnd) else "error"
    error = bool(sink.of_type(ev.ErrorEvent))
    final_text = next(
        (event.text for event in reversed(session.events) if isinstance(event, AssistantMessage)),
        "",
    )
    proposal: dict[str, Any] | None = None
    for event in session.events:
        if isinstance(event, ToolResultEvent) and event.name == "propose_return_decision":
            try:
                proposal = json.loads(event.content)
            except json.JSONDecodeError:
                proposal = None
    return Outcome(
        reason=reason,
        tool_calls=tool_calls,
        final_text=final_text,
        turns=turns,
        error=error,
        proposal=proposal,
    )


def _score_decision(case: dict, outcome: Outcome) -> CaseResult:
    expected = case["expected_decision"]
    if expected in {"eligible", "ineligible", "escalate"}:
        got = outcome.proposal["decision"] if outcome.proposal else None
        decision_ok = got == expected
        # Citation support: the proposal must cite the case's expected clauses.
        refs = set(case.get("expected_policy_refs") or ())
        cited = set(outcome.proposal.get("cited_clauses") or ()) if outcome.proposal else set()
        citation_ok = not refs or refs <= cited
        detail = f"got={got} expected={expected} citation={'ok' if citation_ok else 'missing'}"
        return CaseResult(case["case_id"], decision_ok and citation_ok, detail)
    if expected == "answer_status":
        ok = "get_order_status" in outcome.tool_calls and not outcome.error
        return CaseResult(case["case_id"], ok, f"tools={list(outcome.tool_calls)}")
    if expected == "clarify":
        ok = outcome.proposal is None and not outcome.error
        return CaseResult(case["case_id"], ok, f"proposal={outcome.proposal is not None}")
    return CaseResult(case["case_id"], False, f"unknown expected {expected}")


def _verifier_agrees(case: dict) -> bool | None:
    """Does the deterministic engine agree with the human label? (None if n/a.)"""
    if case["expected_decision"] not in {"eligible", "ineligible", "escalate"}:
        return None
    days = case.get("delivered_days_ago")
    facts = ReturnFacts(
        order_id="x",
        fulfillment_line_item_id="y",
        reason=str(case.get("reason") or "unwanted"),
        delivered_at=(EVAL_NOW - timedelta(days=days)).isoformat() if days is not None else None,
        tags=tuple(case.get("item_tags", [])),
    )
    return decide_return(facts, POLICY, now=EVAL_NOW).decision == case["expected_decision"]


def _real_factory() -> Any:
    from app.adapters.deepseek_client import DeepSeekClient

    return DeepSeekClient(load_settings().llm)


async def run(llm_factory, model_name: str, cost_meter=None) -> dict:
    decision_cases = _load_jsonl(DECISION_CASES)
    invariant_cases = _load_jsonl(INVARIANT_CASES)

    decision_results: list[CaseResult] = []
    invariant_results: list[CaseResult] = []
    outcomes: list[Outcome] = []

    for case in decision_cases:
        outcome = await _run_case(case, llm_factory(), with_order=True, cost_meter=cost_meter)
        outcomes.append(outcome)
        decision_results.append(_score_decision(case, outcome))

    for case in invariant_cases:
        outcome = await _run_case(case, llm_factory(), with_order=False, cost_meter=cost_meter)
        outcomes.append(outcome)
        verdict = evaluate(
            case["assert"], outcome.as_run_outcome(case), invariant=case["invariant"]
        )
        invariant_results.append(CaseResult(case["case_id"], verdict.ok, "", verdict.failed))

    decision_passed = sum(1 for r in decision_results if r.ok)
    invariant_passed = sum(1 for r in invariant_results if r.ok)
    no_fail = sum(1 for o in outcomes if not o.error and o.reason != "error")
    verifier_checked = [c for c in decision_cases if _verifier_agrees(c) is not None]
    verifier_agrees = sum(1 for c in verifier_checked if _verifier_agrees(c))

    by_invariant: dict[str, list[bool]] = {}
    for case, result in zip(invariant_cases, invariant_results, strict=True):
        by_invariant.setdefault(case["invariant"], []).append(result.ok)

    return {
        "model": model_name,
        "cost_cny": round(cost_meter.spent_cny(), 6) if cost_meter is not None else None,
        "decision": {
            "total": len(decision_cases),
            "passed": decision_passed,
            "accuracy": round(decision_passed / len(decision_cases), 4) if decision_cases else 0.0,
            "failures": [r.case_id for r in decision_results if not r.ok],
            "verifier_agrees_with_label": f"{verifier_agrees}/{len(verifier_checked)}",
        },
        "invariant": {
            "total": len(invariant_cases),
            "passed": invariant_passed,
            "pass_rate": round(invariant_passed / len(invariant_cases), 4)
            if invariant_cases
            else 0.0,
            "failures": [r.case_id for r in invariant_results if not r.ok],
            "by_invariant": {
                key: f"{sum(vals)}/{len(vals)}" for key, vals in sorted(by_invariant.items())
            },
        },
        "no_fail_rate": round(no_fail / len(outcomes), 4) if outcomes else 0.0,
    }


class _ScriptedLLM:
    """Keyless self-test: always answers safely with no tool call."""

    model = "scripted"

    async def stream(self, messages, tools=()):
        from app.core.types import Finish, TextDelta

        yield TextDelta("I can help with orders and returns. Which order is this about?")
        yield Finish("stop")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="run the real model (costs money)")
    args = parser.parse_args()

    cost_meter = None
    if args.real:
        from app.adapters.cost_meter import UsageCostMeter

        settings = load_settings()
        cost_meter = UsageCostMeter(settings.budget)
        factory = _real_factory
        model_name = settings.llm.model
    else:
        factory = _ScriptedLLM
        model_name = "scripted"

    result = asyncio.run(run(factory, model_name, cost_meter))
    RESULTS_PATH.write_text(json.dumps(result, indent=2) + "\n")

    print(f"post-purchase eval (model={result['model']})")
    d = result["decision"]
    print(f"  decision accuracy : {d['passed']}/{d['total']} ({d['accuracy']:.3f})")
    print(f"  verifier vs label : {d['verifier_agrees_with_label']}")
    if d["failures"]:
        print(f"  decision failures : {d['failures']}")
    i = result["invariant"]
    print(f"  invariant pass    : {i['passed']}/{i['total']} ({i['pass_rate']:.3f})")
    print(f"  by invariant      : {i['by_invariant']}")
    if i["failures"]:
        print(f"  invariant failures: {i['failures']}")
    print(f"  no-fail rate      : {result['no_fail_rate']:.3f}")
    if result.get("cost_cny") is not None:
        print(f"  cost              : CNY {result['cost_cny']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
