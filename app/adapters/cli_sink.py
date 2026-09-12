"""CLI event sink: Service Provider for :class:`app.ports.event_sink.EventSink`.

Renders agent events to stdout. Useful for local runs and debugging.
"""

from __future__ import annotations

from app.core import events as ev


class CliSink:
    async def emit(self, event: ev.AgentEvent) -> None:
        if isinstance(event, ev.TextDelta):
            print(event.text, end="", flush=True)
        elif isinstance(event, ev.ToolCallStarted):
            print(f"\n[tool] {event.name} {event.arguments}")
        elif isinstance(event, ev.ToolResult):
            print(f"[tool:{event.status}] {event.summary}")
        elif isinstance(event, ev.UIComponent):
            print(f"[ui] {event.component}")
        elif isinstance(event, ev.ErrorEvent):
            print(f"[error] {event.message}")
        elif isinstance(event, ev.TurnEnd):
            print(f"\n[turn end: {event.reason}]")


class ListSink:
    """Collects events for assertions in tests."""

    def __init__(self) -> None:
        self.events: list[ev.AgentEvent] = []

    async def emit(self, event: ev.AgentEvent) -> None:
        self.events.append(event)

    def of_type(self, cls: type) -> list:
        return [e for e in self.events if isinstance(e, cls)]
