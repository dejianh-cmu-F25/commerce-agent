"""Session log: the source of truth for what the model sees.

The log is an append-only list of durable events. ``derive_messages`` is the
**only** way to build model messages (constitution SL-1). Cart and provenance
are derived state, kept alongside the log.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.types import Message, ToolCall


@dataclass
class UserMessage:
    text: str


@dataclass
class AssistantMessage:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ToolResultEvent:
    call_id: str
    name: str
    content: str
    status: str = "ok"  # "ok" | "blocked" | "error"


SessionEvent = UserMessage | AssistantMessage | ToolResultEvent


@dataclass
class CartLine:
    product_id: str
    title: str
    quantity: int
    unit_price: float


@dataclass
class Session:
    id: str
    events: list[SessionEvent] = field(default_factory=list)
    cart: list[CartLine] = field(default_factory=list)
    provenance: set[str] = field(default_factory=set)

    def append(self, event: SessionEvent) -> None:
        self.events.append(event)

    def remember_ids(self, ids: list[str]) -> None:
        self.provenance.update(ids)

    def knows(self, product_id: str) -> bool:
        return product_id in self.provenance


def derive_messages(session: Session, system_prompt: str) -> list[Message]:
    """Project the model message history from the session log.

    This is the single construction path for model input (SL-1).
    """
    messages: list[Message] = [Message(role="system", content=system_prompt)]
    for event in session.events:
        if isinstance(event, UserMessage):
            messages.append(Message(role="user", content=event.text))
        elif isinstance(event, AssistantMessage):
            messages.append(
                Message(role="assistant", content=event.text, tool_calls=list(event.tool_calls))
            )
        elif isinstance(event, ToolResultEvent):
            messages.append(
                Message(
                    role="tool",
                    content=event.content,
                    tool_call_id=event.call_id,
                    name=event.name,
                )
            )
    return messages
