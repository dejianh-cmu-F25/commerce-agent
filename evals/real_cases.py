"""Parameterized real-eval cases (features 023, 024).

Templates instantiate concrete, outcome-checked cases per seed; the template
**name** is stable so reliability aggregates across parameter variants (the
book's parameterized design, which prevents memorization and makes cross-seed
comparison fair). Construction is pure and reproducible.
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
    max_price: float | None = None
    min_cart_items: int = 0


_ITEMS = [
    ("2-Person Tent", "P-101"),
    ("Down Sleeping Bag", "P-102"),
    ("Trail Backpack 40L", "P-104"),
    ("Insulated Water Bottle", "P-105"),
]
_BUDGETS = [150.0, 200.0, 250.0]
_TOPICS = [("shipping", "shipping"), ("returns", "return"), ("warranty", "warranty")]
_FAKE_IDS = ["P-999", "P-000", "P-123"]


def build_cases(seed: int) -> list[RealCase]:
    """Instantiate the templates for a seed (deterministic, paired)."""
    item, item_id = _ITEMS[seed % len(_ITEMS)]
    budget = _BUDGETS[seed % len(_BUDGETS)]
    topic, keyword = _TOPICS[seed % len(_TOPICS)]
    fake_id = _FAKE_IDS[seed % len(_FAKE_IDS)]

    return [
        RealCase(
            name="budget_search",
            user_text=f"I need camping gear under ${budget:.0f}",
            essential_tools=("search_products",),
            essential_components=("products",),
            max_price=budget,
        ),
        RealCase(
            name="multi_item_cart",
            user_text="Build me a cart with gear for a 2-day hike",
            essential_tools=("add_to_cart",),
            essential_components=("cart",),
            min_cart_items=2,
        ),
        RealCase(
            name="add_named_item",
            user_text=f"Add the {item} to my cart",
            essential_tools=("add_to_cart",),
            essential_components=("cart",),
            cart_contains=(item_id,),
        ),
        RealCase(
            name="policy_question",
            user_text=f"What is your {topic} policy?",
            essential_tools=("search_knowledge",),
            answer_contains=(keyword,),
        ),
        RealCase(
            name="refuse_out_of_window",
            user_text="I want to return the backpack from order O-1002",
            essential_tools=("list_orders",),
            forbidden_components=("return",),
        ),
        RealCase(
            name="ungrounded_rejected",
            user_text=f"Add product {fake_id} to my cart",
            forbidden_components=("cart",),
            must_have_empty_cart=True,
        ),
    ]


CASE_NAMES: list[str] = [case.name for case in build_cases(0)]
