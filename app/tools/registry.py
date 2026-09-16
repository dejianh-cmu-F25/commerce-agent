"""Tool registry and execution.

A tool pairs a model-facing ToolSpec with a handler. The registry is the only
place tools are looked up; the executor refuses unknown names (tool surface is
a function of configuration, PB-1).

Pluggable gates (046 hardening): when a :class:`~app.gates.registry.GateSet` is
injected, the registry runs the gates that apply to the tool **before** the
handler, at this single choke point -- so no surface can forget to enforce a
gate. A tool declares its ``effect`` (read / write / proposal / irreversible) and
optionally the server-issued id arguments it writes (``id_args``) and a
``context`` builder for gates that need domain facts.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.gates.base import GATED_EFFECTS, GateContext, GateResult
from app.gates.pipeline import GatePipeline
from app.gates.registry import GateSet


@dataclass
class ToolResult:
    content: str
    status: str = "ok"  # "ok" | "blocked" | "error"
    # Optional UI hint: the loop forwards this to the surface as a UIComponent.
    # The loop never interprets it (keeps the loop generic, P2/P5, WV-3).
    component: str | None = None
    payload: dict[str, Any] | None = None
    # The gate that blocked this call (observability; SC-2).
    blocked_by: str | None = None


# A handler may take (arguments, session) or, when it consumes the resolved gate
# context, (arguments, session, context).
ToolHandler = Callable[..., Awaitable[ToolResult]]
ContextBuilder = Callable[[str, dict[str, Any], Session], Awaitable[GateContext]]


class ToolArgumentError(Exception):
    """The tool's arguments are unusable.

    Raised by a context builder before the gates run, so a malformed call returns
    the tool's own error instead of a gate's verdict (the model's args are checked
    first, exactly as the handler used to do). ``content`` is the tool result body
    (a string as-is, or a dict serialized to JSON).
    """

    def __init__(self, content: str | dict[str, Any], status: str = "error") -> None:
        text = json.dumps(content) if isinstance(content, dict) else content
        super().__init__(text)
        self.content = text
        self.status = status


@dataclass
class Tool:
    spec: ToolSpec
    handler: ToolHandler
    effect: str = "read"
    id_args: tuple[str, ...] = ()
    context: ContextBuilder | None = None
    consumes_context: bool = False
    # Explicitly exempt from the fail-closed rule (must be justified in review).
    ungated: bool = False


class ToolRegistry:
    def __init__(self, gates: GateSet | None = None, *, hit_policy: str = "first") -> None:
        self._tools: dict[str, Tool] = {}
        self._gates = gates
        self._hit_policy = hit_policy

    def register(
        self,
        spec: ToolSpec,
        handler: ToolHandler,
        *,
        effect: str = "read",
        id_args: tuple[str, ...] = (),
        context: ContextBuilder | None = None,
        consumes_context: bool = False,
        ungated: bool = False,
    ) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = Tool(
            spec=spec,
            handler=handler,
            effect=effect,
            id_args=id_args,
            context=context,
            consumes_context=consumes_context,
            ungated=ungated,
        )

    def specs(self) -> list[ToolSpec]:
        return [t.spec for t in self._tools.values()]

    def effects(self) -> dict[str, str]:
        """Tool name -> effect (used by the gate-coverage meta-test)."""
        return {name: tool.effect for name, tool in self._tools.items()}

    def gated_uncovered(self) -> list[str]:
        """Money-adjacent tools with no covering gate (must be empty in production)."""
        if self._gates is None:
            return []
        return [
            name
            for name, tool in self._tools.items()
            if tool.effect in GATED_EFFECTS
            and not tool.ungated
            and not self._gates.covers(name, tool.effect)
        ]

    def has(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, arguments: dict[str, Any], session: Session) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(content=f"Unknown tool: {name}", status="error")

        context: GateContext | None = None
        if tool.consumes_context or self._gates is not None:
            try:
                context = await self._build_context(tool, name, arguments, session)
            except ToolArgumentError as exc:
                return ToolResult(content=exc.content, status=exc.status)

        if self._gates is not None:
            selected = self._gates.select(name, tool.effect)
            if not selected and tool.effect in GATED_EFFECTS and not tool.ungated:
                # Fail closed: a money-adjacent tool with no gate is refused.
                return ToolResult(
                    content=json.dumps({"error": f"no gate covers the {tool.effect} tool {name}"}),
                    status="error",
                    blocked_by="",
                )
            if selected and context is not None:
                verdict = GatePipeline(selected, self._hit_policy).run(context)
                if not verdict.allowed:
                    return self._blocked(verdict)
                context.gate_clauses = verdict.cited_clauses

        try:
            if tool.consumes_context:
                return await tool.handler(arguments, session, context)
            return await tool.handler(arguments, session)
        except Exception as exc:  # tool errors never end the turn (FR-006)
            return ToolResult(content=f"Tool {name} failed: {exc}", status="error")

    async def _build_context(
        self, tool: Tool, name: str, arguments: dict[str, Any], session: Session
    ) -> GateContext:
        if tool.context is not None:
            context = await tool.context(name, arguments, session)
        else:
            context = GateContext(session=session)
        # Fill the plugin fields the tool did not set.
        context.tool = context.tool or name
        context.effect = tool.effect
        context.arguments = context.arguments or dict(arguments)
        context.now = context.now or datetime.now(UTC)
        if not context.ids and tool.id_args:
            context.ids = [
                str(arguments[key]) for key in tool.id_args if arguments.get(key) is not None
            ]
        return context

    def _blocked(self, verdict: GateResult) -> ToolResult:
        if verdict.payload is not None:
            content = json.dumps(verdict.payload)
        else:
            content = json.dumps({"error": f"blocked by {verdict.gate}", "reason": verdict.reason})
        return ToolResult(
            content=content,
            status=verdict.status,
            component=verdict.component,
            payload=verdict.payload,
            blocked_by=verdict.gate or None,
        )
