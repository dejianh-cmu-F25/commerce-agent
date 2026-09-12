"""Gold scenarios for the keyless evaluation harness (P7, TT-2).

Each scenario scripts the model's turns and declares the deterministic outcomes
to assert: the tool sequence, the rendered components, and the cart state. Model
prose is never asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.adapters.mock_llm import MockTurn, text_turn, tool_turn


@dataclass
class Scenario:
    name: str
    user_text: str
    turns: list[MockTurn]
    expect_tools: list[str]
    expect_components: list[str] = field(default_factory=list)
    expect_cart: list[tuple[str, int]] = field(default_factory=list)
    # Customer memory (feature 013): seed facts for the eval customer, then
    # assert facts stored from the turn and facts recalled into its context.
    seed_memory: list[tuple[str, str]] = field(default_factory=list)
    expect_memory: list[str] = field(default_factory=list)
    expect_recall: list[str] = field(default_factory=list)


_SEARCH = tool_turn("search_products", '{"query": "tent"}', call_id="c1")
_ADD = tool_turn("add_to_cart", '{"product_id": "P-101"}', call_id="c2")
_CHECKOUT = tool_turn("render_checkout", "{}", call_id="c3")
_DONE = text_turn("Done.")

SCENARIOS: list[Scenario] = [
    Scenario(
        name="search_only",
        user_text="I need a tent",
        turns=[_SEARCH, _DONE],
        expect_tools=["search_products"],
        expect_components=["products"],
    ),
    Scenario(
        name="add_to_cart",
        user_text="add the tent to my cart",
        turns=[_SEARCH, _ADD, _DONE],
        expect_tools=["search_products", "add_to_cart"],
        expect_components=["products", "cart"],
        expect_cart=[("P-101", 1)],
    ),
    Scenario(
        name="ungrounded_add_rejected",
        user_text="add product P-999",
        turns=[tool_turn("add_to_cart", '{"product_id": "P-999"}', call_id="c9"), _DONE],
        expect_tools=["add_to_cart"],
        expect_components=[],
        expect_cart=[],
    ),
    Scenario(
        name="checkout_render",
        user_text="add the tent and check out",
        turns=[_SEARCH, _ADD, _CHECKOUT, _DONE],
        expect_tools=["search_products", "add_to_cart", "render_checkout"],
        expect_components=["products", "cart", "checkout"],
        expect_cart=[("P-101", 1)],
    ),
    Scenario(
        name="merchant_stage",
        user_text="set the tent price to 199",
        turns=[
            tool_turn(
                "propose_price_change",
                '{"product_id": "P-101", "price": 199}',
                call_id="m1",
            ),
            _DONE,
        ],
        expect_tools=["propose_price_change"],
        expect_components=[],
        expect_cart=[],
    ),
    Scenario(
        name="knowledge_answer",
        user_text="what is your return policy?",
        turns=[tool_turn("search_knowledge", '{"query": "return policy"}', call_id="k1"), _DONE],
        expect_tools=["search_knowledge"],
        expect_components=[],
        expect_cart=[],
    ),
    Scenario(
        name="memory_extract",
        user_text="I usually wear size M",
        turns=[_DONE],
        expect_tools=[],
        expect_memory=["Wears size M"],
    ),
    Scenario(
        name="memory_recall",
        user_text="hello",
        turns=[_DONE],
        expect_tools=[],
        seed_memory=[("profile", "Wears size M")],
        expect_recall=["Wears size M"],
    ),
    Scenario(
        name="order_status",
        user_text="where is my order?",
        turns=[
            tool_turn("list_orders", "{}", call_id="o1"),
            tool_turn("get_order_status", '{"order_id": "O-1001"}', call_id="o2"),
            _DONE,
        ],
        expect_tools=["list_orders", "get_order_status"],
        expect_components=["orders", "order"],
    ),
    Scenario(
        name="start_return",
        user_text="I want to return the tent",
        turns=[
            tool_turn("list_orders", "{}", call_id="o1"),
            tool_turn(
                "start_return", '{"order_id": "O-1001", "product_id": "P-101"}', call_id="o2"
            ),
            _DONE,
        ],
        expect_tools=["list_orders", "start_return"],
        expect_components=["orders", "return"],
    ),
    Scenario(
        name="return_out_of_window",
        user_text="I want to return the backpack",
        turns=[
            tool_turn("list_orders", "{}", call_id="o1"),
            tool_turn(
                "start_return", '{"order_id": "O-1002", "product_id": "P-104"}', call_id="o2"
            ),
            _DONE,
        ],
        expect_tools=["list_orders", "start_return"],
        expect_components=["orders"],
    ),
]
