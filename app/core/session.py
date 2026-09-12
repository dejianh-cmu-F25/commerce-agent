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


@dataclass
class MemoryNote:
    """Facts recalled from customer memory, recorded when injected (SL-1).

    Memory is model-visible context, so it lives in the log: ``derive_messages``
    folds it into the system message, keeping the context reconstructable.
    """

    facts: list[str] = field(default_factory=list)


SessionEvent = UserMessage | AssistantMessage | ToolResultEvent | MemoryNote


@dataclass
class CartLine:
    product_id: str
    title: str
    quantity: int
    unit_price: float


@dataclass
class Session:
    id: str
    customer_id: str = ""  # opaque client id; empty means memory-disabled (013)
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

    This is the single construction path for model input (SL-1). Recalled
    memory (:class:`MemoryNote`) is folded into the system message, so memory
    context is derived from the log like everything else.
    """
    memory_lines: list[str] = []
    for event in session.events:
        if isinstance(event, MemoryNote):
            memory_lines.extend(event.facts)

    system_content = system_prompt
    if memory_lines:
        system_content = (
            f"{system_prompt}\n\n## What you remember about this customer\n"
            + "\n".join(f"- {fact}" for fact in memory_lines)
        )

    messages: list[Message] = [Message(role="system", content=system_content)]
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
