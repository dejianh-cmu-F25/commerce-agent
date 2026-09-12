"""Tool registry and execution.

A tool pairs a model-facing ToolSpec with a handler. The registry is the only
place tools are looked up; the executor refuses unknown names (tool surface is
a function of configuration, PB-1).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec


@dataclass
class ToolResult:
    content: str
    status: str = "ok"  # "ok" | "blocked" | "error"
    # Optional UI hint: the loop forwards this to the surface as a UIComponent.
    # The loop never interprets it (keeps the loop generic, P2/P5, WV-3).
    component: str | None = None
    payload: dict[str, Any] | None = None


ToolHandler = Callable[[dict[str, Any], Session], Awaitable[ToolResult]]


@dataclass
class Tool:
    spec: ToolSpec
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, spec: ToolSpec, handler: ToolHandler) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = Tool(spec=spec, handler=handler)

    def specs(self) -> list[ToolSpec]:
        return [t.spec for t in self._tools.values()]

    def has(self, name: str) -> bool:
        return name in self._tools

    async def execute(self, name: str, arguments: dict[str, Any], session: Session) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(content=f"Unknown tool: {name}", status="error")
        try:
            return await tool.handler(arguments, session)
        except Exception as exc:  # tool errors never end the turn (FR-006)
            return ToolResult(content=f"Tool {name} failed: {exc}", status="error")
