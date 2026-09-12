"""Deterministic mock LLM for tests and keyless runs.

A scripted list of turns; each turn is a list of events. This lets us evaluate
the harness without a provider (constitution HR-8, TT-2).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.core.types import (
    Finish,
    LLMEvent,
    Message,
    TextDelta,
    ToolCall,
    ToolCallComplete,
    ToolSpec,
)

# A turn is either text, a tool call, or both. Kept as plain data so fixtures
# can be loaded from JSON later.
MockTurn = list[LLMEvent]


class MockLLMClient:
    """Replays a scripted sequence of turns, one per ``stream`` call."""

    def __init__(self, turns: list[MockTurn]) -> None:
        self._turns = list(turns)
        self._calls = 0

    async def stream(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
    ) -> AsyncIterator[LLMEvent]:
        index = min(self._calls, len(self._turns) - 1) if self._turns else -1
        self._calls += 1
        if index < 0:
            yield TextDelta("(no scripted response)")
            yield Finish("stop")
            return
        for event in self._turns[index]:
            yield event


def text_turn(text: str) -> MockTurn:
    return [TextDelta(text), Finish("stop")]


def tool_turn(name: str, arguments: str, call_id: str = "call_1") -> MockTurn:
    return [
        ToolCallComplete(ToolCall(id=call_id, name=name, arguments=arguments)),
        Finish("tool_calls"),
    ]
