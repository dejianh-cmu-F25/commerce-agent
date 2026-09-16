"""LLM listwise reranker (feature 046, step A6).

First-stage retrieval optimises recall; the top of the list is where precision
decays. A reranker re-scores the candidate set against the query with a stronger
(and more expensive) model, which every production search stack does at this
point. This one is **listwise**: candidate titles go in once, one ranked order
comes back, so a query costs a single call rather than one per candidate.

Two properties the caller depends on:

- **Never lose results**: unparseable output, a refusal, or a provider error
  returns the original order. A reranker may not make search worse by failing.
- **Never hide the cost**: this runs *outside* the agent loop, which is where the
  cost meter is normally fed, so it records its own usage. Without that the
  reported per-run cost would understate every reranked search.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from app.core.types import Message, TextDelta, Usage
from app.ports.cost_meter import CostMeter
from app.ports.llm import LLMClient

_ORDER = re.compile(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]")

PROMPT = """You are ranking search results for an online store.

Customer query: {query}

Candidates (numbered, best guess first):
{candidates}

Return the candidate numbers ordered from most to least relevant to the query.
Use every number exactly once. Answer with the JSON array of numbers only, for
example: [3, 1, 2]
"""


def _candidate_line(index: int, candidate: Any) -> str:
    """Prefer the richest text available: a dict may carry attributes, else str()."""
    if isinstance(candidate, dict):
        parts = [
            str(candidate.get("text") or candidate.get("title") or ""),
            str(candidate.get("brand") or ""),
            str(candidate.get("category") or ""),
        ]
        text = " — ".join(part for part in parts if part)
    else:
        text = str(candidate)
    return f"{index}. {' '.join(text.split())[:200]}"


def parse_order(text: str, size: int) -> list[int] | None:
    """The first JSON array of indices in ``text``, as 0-based positions.

    Returns ``None`` when nothing usable is found or the result is not a
    permutation of the candidates, so the caller keeps the original order.
    """
    for match in _ORDER.finditer(text):
        try:
            numbers = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        positions = [n - 1 for n in numbers if isinstance(n, int)]
        if sorted(positions) == list(range(size)):
            return positions
    return None


class LlmListwiseReranker:
    def __init__(
        self,
        llm: LLMClient,
        *,
        top_k: int = 5,
        max_candidates: int = 20,
        cost_meter: CostMeter | None = None,
        timeout_s: float = 20.0,
    ) -> None:
        self._llm = llm
        self._top_k = top_k
        self._max_candidates = max_candidates
        self._cost_meter = cost_meter
        # A hung provider must not hang search: on timeout, keep the retrieval order.
        self._timeout_s = timeout_s
        self.calls = 0
        self.timeouts = 0

    async def rerank(
        self, query: str, candidates: list[Any], top_k: int | None = None
    ) -> list[Any]:
        limit = top_k or self._top_k
        window = candidates[: self._max_candidates]
        if len(window) < 2 or not query.strip():
            return candidates[:limit]

        prompt = PROMPT.format(
            query=query,
            candidates="\n".join(
                _candidate_line(index, candidate) for index, candidate in enumerate(window, 1)
            ),
        )
        text = ""
        stream = None
        try:
            self.calls += 1
            stream = self._llm.stream([Message(role="user", content=prompt)], [])

            async def consume() -> str:
                buffer = ""
                async for event in stream:  # type: ignore[union-attr]
                    if isinstance(event, Usage) and self._cost_meter is not None:
                        self._cost_meter.record(event)
                    elif isinstance(event, TextDelta):
                        buffer += event.text
                return buffer

            text = await asyncio.wait_for(consume(), timeout=self._timeout_s)
        except TimeoutError:
            self.timeouts += 1
            return candidates[:limit]
        except Exception:
            # A reranker must never break search: fall back to the retrieval order.
            return candidates[:limit]
        finally:
            aclose = getattr(stream, "aclose", None)
            if aclose is not None:
                try:
                    await aclose()
                except Exception:
                    pass

        order = parse_order(text, len(window))
        if order is None:
            return candidates[:limit]
        ranked = [window[position] for position in order]
        ranked.extend(candidates[len(window) :])
        return ranked[:limit]
