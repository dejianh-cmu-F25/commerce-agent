"""LLM query understanding (feature 047): rewrite a need into retrieval terms.

A shopper's need ("something to keep dog hair off my clothes while grooming him")
rarely shares words with the product text, so the request is rewritten into the
vocabulary a description or a review would use (the HyDE idea), and any hard
constraint is extracted as a filter.

Two properties the caller relies on:

- **Never break search**: a provider error, a timeout, or unparseable output falls
  back to the original query with no filter (RD-1).
- **Never hide the cost**: it runs outside the agent loop, so it records its own
  usage against the cost meter.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from app.core.types import Message, TextDelta, Usage
from app.ports.cost_meter import CostMeter
from app.ports.llm import LLMClient
from app.ports.query_understanding import QueryPlan

_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def parse_plan(text: str) -> dict[str, Any] | None:
    """The first JSON object in ``text``, or ``None`` when there is none."""
    match = _OBJECT.search(text or "")
    if match is None:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


class LlmQueryUnderstanding:
    name = "llm"

    def __init__(
        self,
        llm: LLMClient,
        prompt: str,
        *,
        cost_meter: CostMeter | None = None,
        timeout_s: float = 15.0,
    ) -> None:
        self._llm = llm
        self._prompt = prompt
        self._cost_meter = cost_meter
        self._timeout_s = timeout_s
        self.calls = 0
        self.fallbacks = 0

    async def _complete(self, prompt: str) -> str:
        stream = None
        try:
            stream = self._llm.stream([Message(role="user", content=prompt)], [])

            async def consume() -> str:
                buffer = ""
                async for event in stream:  # type: ignore[union-attr]
                    if isinstance(event, Usage) and self._cost_meter is not None:
                        self._cost_meter.record(event)
                    elif isinstance(event, TextDelta):
                        buffer += event.text
                return buffer

            return await asyncio.wait_for(consume(), timeout=self._timeout_s)
        finally:
            aclose = getattr(stream, "aclose", None)
            if aclose is not None:
                try:
                    await aclose()
                except Exception:
                    pass

    async def understand(self, query: str) -> QueryPlan:
        self.calls += 1
        try:
            text = await self._complete(self._prompt.format(query=query))
        except Exception:  # noqa: BLE001 - a rewrite must never break search (RD-1)
            self.fallbacks += 1
            return QueryPlan(terms=query, note="rewrite failed; original query")
        data = parse_plan(text)
        if data is None:
            self.fallbacks += 1
            return QueryPlan(terms=query, note="rewrite unparseable; original query")
        terms = str(data.get("query") or query).strip() or query
        where: dict[str, Any] = {}
        max_price = data.get("max_price")
        if isinstance(max_price, (int, float)) and max_price > 0:
            where["price"] = {"$lte": float(max_price)}
        return QueryPlan(terms=terms, where=where, note="llm rewrite")
