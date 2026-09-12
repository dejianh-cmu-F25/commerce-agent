"""Outcome-based cases for the opt-in real-model eval (feature 023).

Success is judged on deterministic outcomes (essential tools, components, cart
contents, grounded answer strings, and forbidden components), never on prose or
exact tool sequences (TT-2). The negative cases test the harness's guardrails:
an out-of-window return must not render, and an ungrounded id must not add.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RealCase:
    name: str
    user_text: str
    essential_tools: tuple[str, ...] = ()
    essential_components: tuple[str, ...] = ()
    cart_contains: tuple[str, ...] = ()
    answer_contains: tuple[str, ...] = ()
    forbidden_components: tuple[str, ...] = ()
    must_have_empty_cart: bool = False


REAL_CASES: list[RealCase] = [
    RealCase("search", "I need a 2-person tent under $250", ("search_products",), ("products",)),
    RealCase(
        "cart",
        "Add the 2-Person Tent to my cart",
        ("add_to_cart",),
        ("cart",),
        ("P-101",),
    ),
    RealCase("knowledge", "What is your return policy?", ("search_knowledge",), (), (), ("30",)),
    RealCase("order_status", "Where is my order?", ("list_orders",), ("orders",)),
    RealCase(
        "return", "I want to return the tent from order O-1001", ("start_return",), ("return",)
    ),
    RealCase(
        "refuse_out_of_window",
        "I want to return the backpack from order O-1002",
        ("list_orders",),
        forbidden_components=("return",),
    ),
    RealCase(
        "ungrounded_rejected",
        "Add product P-999 to my cart",
        forbidden_components=("cart",),
        must_have_empty_cart=True,
    ),
]
