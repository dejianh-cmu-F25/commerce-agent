"""Shared domain types for the agent loop.

Kept dependency-free so core and ports can both import them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

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
