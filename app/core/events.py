"""Agent events emitted by the loop and rendered by surfaces (web, cli).

Events are the loop's only outward channel. Surfaces subscribe through an
EventSink; the loop never imports a surface (PB-2, HR-11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TurnStart:
    turn_id: str


@dataclass
class TextDelta:
    text: str


@dataclass
class ToolCallStarted:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    name: str
    status: str  # "ok" | "blocked" | "error"
    summary: str = ""


@dataclass
class UIComponent:
    component: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class CartUpdate:
    cart: dict[str, Any] = field(default_factory=dict)


@dataclass
class TurnEnd:
    turn_id: str
    reason: str


@dataclass
class ErrorEvent:
    message: str


@dataclass
class UsageReported:
    spent_cny: float
    limit_cny: float
    remaining_cny: float


@dataclass
class BudgetExceeded:
    spent_cny: float
    limit_cny: float


AgentEvent = (
    TurnStart
    | TextDelta
    | ToolCallStarted
    | ToolResult
    | UIComponent
    | CartUpdate
    | UsageReported
    | BudgetExceeded
    | TurnEnd
    | ErrorEvent
)


def to_wire(event: AgentEvent) -> dict[str, Any]:
    """Serialize an event for transport (SSE / CLI)."""
    payload = {k: v for k, v in event.__dict__.items()}
    return {"type": type(event).__name__, "data": payload}
