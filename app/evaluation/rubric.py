"""Rubric LLM-as-a-Judge with a veto (feature 023, book ch.7).

Dimensions: grounding (essential), correctness (essential), policy_compliance
(important), completeness (important), tone (optional). Veto: any fabricated
price, stock, or policy fact fails the answer regardless of the other scores.

The judge is a model call; when it is unavailable or returns malformed output,
:func:`deterministic_grade` is the fallback (RD-1). The judge prompt is external
(PB-4).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from app.core.prompts import load_prompt
from app.core.types import Finish, Message, TextDelta
from app.ports.llm import LLMClient

DIMENSIONS = ("grounding", "correctness", "policy_compliance", "completeness", "tone")
_PRICE = re.compile(r"\$\d+(?:\.\d+)?")


@dataclass
class JudgeResult:
    scores: dict[str, int] = field(default_factory=dict)
    veto: bool = False
    rationale: str = ""
    judge: str = "deterministic"


def _score(value: object) -> int:
    try:
        return max(0, min(4, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _extract_json(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def deterministic_grade(answer: str, grounded_facts: list[str]) -> JudgeResult:
    """Rule-based fallback: veto if the answer cites a price not in the facts."""
    grounded: set[str] = set()
    for fact in grounded_facts:
        grounded.update(_PRICE.findall(fact))
    fabricated = set(_PRICE.findall(answer)) - grounded
    if fabricated:
        return JudgeResult(veto=True, rationale=f"ungrounded price(s): {sorted(fabricated)}")
    return JudgeResult(
        scores={"grounding": 4 if grounded else 3},
        rationale="rule-based grounding check",
    )


async def judge_answer(
    llm: LLMClient,
    *,
    question: str,
    answer: str,
    context: str,
    grounded_facts: list[str],
    model: str = "deepseek",
) -> JudgeResult:
    """Score an answer with the LLM judge; fall back to rules on any failure."""
    system = load_prompt("judge")
    user = (
        f"Customer question:\n{question}\n\n"
        f"Grounded tool results:\n{context or '(none)'}\n\n"
        f"Agent answer:\n{answer}\n\n"
        "Return JSON only."
    )
    messages = [Message(role="system", content=system), Message(role="user", content=user)]
    text = ""
    try:
        # Drain the stream fully (no early break) so the async generator closes
        # cleanly; the Finish event is last.
        async for event in llm.stream(messages, []):
            if isinstance(event, TextDelta):
                text += event.text
            elif isinstance(event, Finish):
                continue
    except Exception:  # noqa: BLE001 - any judge failure falls back (RD-1)
        return deterministic_grade(answer, grounded_facts)

    data = _extract_json(text)
    if data is None:
        return deterministic_grade(answer, grounded_facts)

    return JudgeResult(
        scores={dimension: _score(data.get(dimension)) for dimension in DIMENSIONS},
        veto=bool(data.get("veto", False)),
        rationale=str(data.get("rationale", ""))[:300],
        judge=model,
    )
