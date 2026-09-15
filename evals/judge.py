#!/usr/bin/env python3
"""LLM-judge alignment against verifiable facts (feature 046, Batch D).

An LLM judge is only useful if its labels track the truth. Here the truth is
**verifiable**: a return answer is consistent when its decision matches the
deterministic policy engine, its price/ids are grounded in the order, and it
cites the clauses that support the decision.

The judge is asked the same question ("is this answer consistent with the tool
facts?"); we then report **precision and recall** of the judge against the
verifiable labels (not raw agreement — the classes are imbalanced, per Hamel
Husain's warning).

Run::

    uv run python evals/judge.py --limit 16
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.evaluation.report_meta import with_marker

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "judge-alignment.md"

JUDGE_PROMPT = """You are auditing an e-commerce assistant's answer.

Order facts (from the tool backend):
{order}

Policy extract (the only source of return rules):
- the return window is 30 days from delivery
- some categories are non-returnable (final sale)
- a restocking fee may apply
- damaged/defective items may be an exception inside the window

The assistant's recorded return proposal: {proposal}

Assistant answer:
{answer}

Question: is the answer CONSISTENT with the order facts and the recorded
proposal? Inconsistent means it invents an order, price or date, states a
decision that differs from the proposal, or asserts a policy rule that is not in
the extract. Answer with JSON only:
{{"consistent": true|false, "reason": "<short>"}}"""


def _oracle_consistent(case: dict, outcome: object) -> bool:
    """Verifiable ground truth: decision matches the label and citations support it."""
    from evals.post_purchase_eval import _score_decision

    if case["expected_decision"] not in {"eligible", "ineligible", "escalate"}:
        return not getattr(outcome, "error", False)
    return _score_decision(case, outcome).ok  # type: ignore[arg-type]


async def _judge(llm: object, case: dict, outcome: object) -> bool | None:
    from app.core.types import Message
    from evals.post_purchase_eval import _backend_for

    backend, order_id = _backend_for(case)
    order = await backend.get_order(order_id)
    facts = "no order on file for this customer"
    if order is not None:
        items = "; ".join(
            f"{line.title} (tags: {', '.join(line.tags) or 'none'})" for line in order.line_items
        )
        facts = (
            f"order {order.id}, status {order.fulfillment_status}, "
            f"delivered_at {order.delivered_at}, items: {items}"
        )
    prompt = JUDGE_PROMPT.format(
        order=facts,
        proposal=json.dumps(getattr(outcome, "proposal", None)),
        answer=getattr(outcome, "final_text", ""),
    )
    text = ""
    async for event in llm.stream([Message(role="user", content=prompt)], []):  # type: ignore[arg-type]
        delta = getattr(event, "text", None)
        if delta:
            text += delta
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        return bool(json.loads(text[start : end + 1]).get("consistent"))
    except json.JSONDecodeError:
        return None


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=16)
    args = parser.parse_args()

    from app.adapters.deepseek_client import DeepSeekClient
    from app.core.settings import load_settings
    from evals.post_purchase_eval import DECISION_CASES, _load_jsonl, _run_case

    settings = load_settings()
    cases = _load_jsonl(DECISION_CASES)[: args.limit]
    judge_llm = DeepSeekClient(settings.llm)

    tp = fp = tn = fn = skipped = 0
    rows: list[str] = []
    for case in cases:
        outcome = await _run_case(case, DeepSeekClient(settings.llm), with_order=True)
        oracle = _oracle_consistent(case, outcome)
        verdict = await _judge(judge_llm, case, outcome)
        if verdict is None:
            skipped += 1
            continue
        if oracle and verdict:
            tp += 1
        elif not oracle and verdict:
            fp += 1
        elif not oracle and not verdict:
            tn += 1
        else:
            fn += 1
        rows.append(
            f"| {case['case_id']} | {'ok' if oracle else 'bad'} | {'ok' if verdict else 'bad'} |"
        )

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    report = (
        f"""# LLM-judge alignment (vs verifiable facts)

- Cases: **{len(cases)}** (post-purchase decision set), skipped (unparseable): {skipped}
- Judge: `{settings.llm.model}`
- Ground truth: **verifiable** (decision matches the policy engine + citation support)

| | judge says consistent | judge says inconsistent |
| --- | --- | --- |
| **verifiable: consistent** | {tp} | {fn} |
| **verifiable: inconsistent** | {fp} | {tn} |

- **Precision: {precision:.3f}**  ·  **Recall: {recall:.3f}**

## Per case

| case | verifiable | judge |
| --- | --- | --- |
"""
        + "\n".join(rows)
        + """

## Notes

- Reporting precision/recall (not raw agreement) because the classes are imbalanced.
- Only the **verifiable** dimensions (decision, citation, grounding) are judged; the
  subjective dimensions (tone, helpfulness) have no objective ground truth and are
  therefore **not** claimed as reliable.
"""
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        with_marker(
            report,
            "evals/judge.py",
            len(cases),
            ["evals/post_purchase_cases.jsonl", "evals/judge.py"],
        )
    )
    print(
        f"judge alignment: precision={precision:.3f} recall={recall:.3f} "
        f"(tp={tp} fp={fp} tn={tn} fn={fn} skipped={skipped})"
    )
    print(f"wrote {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
