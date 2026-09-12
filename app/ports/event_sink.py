"""Event sink capability: Service Definition.

The loop emits AgentEvents; a surface provides a sink that renders or forwards
them (SSE to the browser, lines to a CLI, a list in tests).
"""

from __future__ import annotations

from typing import Protocol

from app.core.events import AgentEvent


class EventSink(Protocol):
    async def emit(self, event: AgentEvent) -> None:
        """Handle one event. Must not raise on normal flow."""
        ...
