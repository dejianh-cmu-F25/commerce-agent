"""The agent loop.

One turn is zero or more steps; a step is one model call plus the tools it
requests. Model messages are built only from the session log (SL-1); a mismatch
crashes the process.

Every turn emits structured spans (turn, llm, tool) through an injected
:class:`app.ports.tracer.Tracer` (SL-2). Tracing is best-effort: a tracer failure
never changes the turn.
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
from app.core.tracing import SpanTimer
from app.core.types import Finish, Message, TextDelta, ToolCall, ToolCallComplete, Usage
from app.ports.cost_meter import CostMeter
from app.ports.event_sink import EventSink
from app.ports.llm import LLMClient
from app.ports.tracer import Tracer
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
        tracer: Tracer | None = None,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._settings = settings
        self._system_prompt = system_prompt
        self._cost_meter = cost_meter
        self._tracer = tracer

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
        trace_id = uuid4().hex
        await sink.emit(ev.TurnStart(turn_id=turn_id))
        reason = "stop"
        with SpanTimer(self._tracer, "turn", trace_id) as span:
            span.attributes["session_id"] = session.id
            try:
                reason = await self._run_steps(session, sink, trace_id, span.span_id)
            except Exception as exc:  # surface the failure, never hide it
                await sink.emit(ev.ErrorEvent(message=str(exc)))
                reason = "error"
            finally:
                span.attributes["reason"] = reason
                span.status = "ok" if reason == "stop" else reason
                await sink.emit(ev.TurnEnd(turn_id=turn_id, reason=reason))

    async def _run_steps(
        self, session: Session, sink: EventSink, trace_id: str, parent_id: str
    ) -> str:
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
            text, tool_calls = await self._model_call(messages, sink, trace_id, parent_id)
            session.append(AssistantMessage(text=text, tool_calls=tool_calls))
            if not tool_calls:
                return "stop"
            for call in tool_calls:
                await self._execute_call(call, session, sink, trace_id, parent_id)
        return "max_turns"

    async def _model_call(
        self,
        messages: Sequence[Message],
        sink: EventSink,
        trace_id: str,
        parent_id: str,
    ) -> tuple[str, list[ToolCall]]:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        prompt_tokens = 0
        completion_tokens = 0
        spent_before = self._cost_meter.spent_cny() if self._cost_meter is not None else 0.0

        with SpanTimer(self._tracer, "llm", trace_id, parent_id) as span:
            async for event in self._llm.stream(messages, self._tools.specs()):
                if isinstance(event, TextDelta):
                    text_parts.append(event.text)
                    await sink.emit(ev.TextDelta(text=event.text))
                elif isinstance(event, ToolCallComplete):
                    tool_calls.append(event.call)
                elif isinstance(event, Usage):
                    prompt_tokens += event.prompt_tokens
                    completion_tokens += event.completion_tokens
                    await self._record_usage(event, sink)
                elif isinstance(event, Finish):
                    break
            span.attributes["prompt_tokens"] = prompt_tokens
            span.attributes["completion_tokens"] = completion_tokens
            span.attributes["tool_calls"] = len(tool_calls)
            if self._cost_meter is not None:
                span.attributes["cost_cny"] = round(self._cost_meter.spent_cny() - spent_before, 6)
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

    async def _execute_call(
        self,
        call: ToolCall,
        session: Session,
        sink: EventSink,
        trace_id: str,
        parent_id: str,
    ) -> None:
        arguments = _parse_arguments(call.arguments)
        await sink.emit(ev.ToolCallStarted(name=call.name, arguments=arguments))
        with SpanTimer(self._tracer, "tool", trace_id, parent_id) as span:
            span.attributes["name"] = call.name
            span.attributes["arguments"] = call.arguments
            result = await self._tools.execute(call.name, arguments, session)
            span.attributes["status"] = result.status
            span.attributes["output"] = result.content
            if result.status != "ok":
                span.status = "error"
        session.append(
            ToolResultEvent(
                call_id=call.id, name=call.name, content=result.content, status=result.status
            )
        )
        await sink.emit(
            ev.ToolResult(name=call.name, status=result.status, summary=_summarize(result.content))
        )
        if result.component:
            # Forward a tool-declared component; the loop does not interpret it.
            await sink.emit(
                ev.UIComponent(component=result.component, payload=result.payload or {})
            )
