"""Shared domain types for the agent loop.

Kept dependency-free so core and ports can both import them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # raw JSON string as produced by the model


@dataclass
class Message:
    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolSpec:
    """A tool exposed to the model (name, description, JSON schema)."""

    name: str
    description: str
    parameters: dict


@dataclass
class Product:
    """A storefront product.

    ``id`` is server-issued; it is the only handle that may enter the session
    (grounding, P4).
    """

    id: str
    title: str
    price: float
    stock: int
    tags: list[str] = field(default_factory=list)

    @property
    def in_stock(self) -> bool:
        return self.stock > 0


# --- Streaming events emitted by an LLM client ---


@dataclass
class TextDelta:
    text: str


@dataclass
class ToolCallComplete:
    call: ToolCall


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0


@dataclass
class Finish:
    reason: str


LLMEvent = TextDelta | ToolCallComplete | Usage | Finish


# --- Observability ---


@dataclass
class Span:
    """One unit of work in a trace (SL-2, OB-1)."""

    trace_id: str
    span_id: str
    name: str
    start_ms: float
    end_ms: float
    parent_id: str | None = None
    status: str = "ok"
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceSummary:
    trace_id: str
    start_ms: float
    duration_ms: float
    span_count: int
    status: str
