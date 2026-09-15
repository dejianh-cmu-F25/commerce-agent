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
    # The first variant's SKU. Imported products store the source ASIN here, which is
    # the key the review store uses - the join between a product and its reviews.
    sku: str = ""

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


@dataclass
class Change:
    """A staged merchant change, applied only after human approval (P3)."""

    id: str
    product_id: str
    kind: str  # "price" | "stock"
    old_value: float
    new_value: float
    status: str  # "pending" | "applied"
    created_at: str


@dataclass
class Chunk:
    """A retrieved knowledge chunk (P4: answers come from these)."""

    id: str
    text: str
    source: str
    score: float = 0.0


@dataclass
class MemoryFact:
    """A durable, customer-grounded statement (feature 013).

    Facts come only from the customer's own text (P4); ``id`` is server-issued.
    ``kind`` is one of ``preference`` | ``constraint`` | ``profile``.
    """

    id: str
    customer_id: str
    kind: str
    text: str
    created_at: str


@dataclass
class OrderItem:
    """A line on an order (feature 014)."""

    product_id: str
    title: str
    quantity: int
    unit_price: float

    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Order:
    """A customer's order in the storefront system of record (feature 014).

    ``id`` is server-issued; it is the only handle that may enter the session
    (grounding, P4). ``status`` is one of ``processing`` | ``shipped`` |
    ``delivered`` | ``cancelled``.
    """

    id: str
    customer_id: str
    status: str
    placed_at: str
    total: float
    delivered_at: str | None = None
    items: list[OrderItem] = field(default_factory=list)


@dataclass
class ReturnRequest:
    """A customer's request to return an item (feature 014).

    A proposal, not a refund: the harness records and renders it; it never
    charges, refunds, or changes the order (P3).
    """

    id: str
    order_id: str
    product_id: str
    status: str  # "requested"
    created_at: str
