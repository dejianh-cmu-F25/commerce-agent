"""LLM capability: Service Definition.

A provider streams text deltas, completed tool calls, and a finish reason.
Adapters (DeepSeek, OpenAI, mock) implement this; the loop only sees it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from app.core.types import LLMEvent, Message, ToolSpec


class LLMClient(Protocol):
    def stream(
        self,
        messages: Sequence[Message],
        tools: Sequence[ToolSpec] = (),
    ) -> AsyncIterator[LLMEvent]:
        """Stream a completion for ``messages``, optionally offering ``tools``."""
        ...
