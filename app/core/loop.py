"""The agent loop.

One turn is zero or more steps; a step is one model call plus the tools it
requests. Model messages are built only from the session log (SL-1); a mismatch
crashes the process.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from uuid import uuid4

from app.core import events as ev
from app.core.session import (
    AssistantMessage,
    Session,
    ToolResultEvent,
    UserMessage,
    derive_messages,
)
from app.core.settings import AgentSettings
from app.core.types import Finish, Message, TextDelta, ToolCall, ToolCallComplete, Usage
from app.ports.cost_meter import CostMeter
from app.ports.event_sink import EventSink
from app.ports.llm import LLMClient
from app.tools.registry import ToolRegistry


class SL1Violation(RuntimeError):
    """Raised when model messages cannot be reconstructed from the session log."""


def _parse_arguments(raw: str) -> dict:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _summarize(content: str, limit: int = 160) -> str:
    return content if len(content) <= limit else content[: limit - 1] + "…"


class Agent:
    """Drives a single conversation over one session."""

    def __init__(
        self,
        *,
        llm: LLMClient,
        tools: ToolRegistry,
        settings: AgentSettings,
        system_prompt: str,
        cost_meter: CostMeter | None = None,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._settings = settings
        self._system_prompt = system_prompt
        self._cost_meter = cost_meter

    def build_request(self, session: Session) -> list[Message]:
        """Build model messages from the session log (the only path, SL-1)."""
        messages = derive_messages(session, self._system_prompt)
        # SL-1 guard: re-derive and compare. A mismatch means a second
        # construction path has crept in; crash rather than send wrong context.
        if messages != derive_messages(session, self._system_prompt):
            raise SL1Violation("model messages are not reconstructable from the session log")
        return messages

    async def stream_turn(self, session: Session, user_text: str, sink: EventSink) -> None:
        session.append(UserMessage(user_text))
        turn_id = uuid4().hex[:8]
        await sink.emit(ev.TurnStart(turn_id=turn_id))
        reason = "stop"
        try:
            reason = await self._run_steps(session, sink)
        except Exception as exc:  # surface the failure, never hide it
            await sink.emit(ev.ErrorEvent(message=str(exc)))
            reason = "error"
        finally:
            await sink.emit(ev.TurnEnd(turn_id=turn_id, reason=reason))

    async def _run_steps(self, session: Session, sink: EventSink) -> str:
        for _ in range(self._settings.max_turns):
            if self._cost_meter is not None and self._cost_meter.over_budget():
                await sink.emit(
                    ev.BudgetExceeded(
                        spent_cny=self._cost_meter.spent_cny(),
                        limit_cny=self._cost_meter.limit_cny(),
                    )
                )
                return "budget"
            messages = self.build_request(session)
            text, tool_calls = await self._model_call(messages, sink)
            session.append(AssistantMessage(text=text, tool_calls=tool_calls))
            if not tool_calls:
                return "stop"
            for call in tool_calls:
                await self._execute_call(call, session, sink)
        return "max_turns"

    async def _model_call(
        self, messages: Sequence[Message], sink: EventSink
    ) -> tuple[str, list[ToolCall]]:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        async for event in self._llm.stream(messages, self._tools.specs()):
            if isinstance(event, TextDelta):
                text_parts.append(event.text)
                await sink.emit(ev.TextDelta(text=event.text))
            elif isinstance(event, ToolCallComplete):
                tool_calls.append(event.call)
            elif isinstance(event, Usage):
                await self._record_usage(event, sink)
            elif isinstance(event, Finish):
                break
        return "".join(text_parts), tool_calls

    async def _record_usage(self, usage: Usage, sink: EventSink) -> None:
        if self._cost_meter is None:
            return
        self._cost_meter.record(usage)
        await sink.emit(
            ev.UsageReported(
                spent_cny=round(self._cost_meter.spent_cny(), 6),
                limit_cny=self._cost_meter.limit_cny(),
                remaining_cny=round(self._cost_meter.remaining_cny(), 6),
            )
        )

    async def _execute_call(self, call: ToolCall, session: Session, sink: EventSink) -> None:
        arguments = _parse_arguments(call.arguments)
        await sink.emit(ev.ToolCallStarted(name=call.name, arguments=arguments))
        result = await self._tools.execute(call.name, arguments, session)
        session.append(
            ToolResultEvent(
                call_id=call.id, name=call.name, content=result.content, status=result.status
            )
        )
        await sink.emit(
            ev.ToolResult(name=call.name, status=result.status, summary=_summarize(result.content))
        )
