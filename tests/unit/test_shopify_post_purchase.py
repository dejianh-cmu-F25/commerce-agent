"""Shopify post-purchase reads (feature 045): transport + mapping, keyless."""

from __future__ import annotations

import httpx
import pytest

from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.adapters.shopify_client import ShopifyAdminClient, ShopifyError
from app.adapters.shopify_post_purchase import ShopifyPostPurchase
from app.ports.post_purchase import LineItem, OrderView, ReturnableItem

ORDER_RESPONSE = {
    "data": {
        "order": {
            "id": "gid://shopify/Order/1",
            "name": "#1001",
            "createdAt": "2026-08-01T10:00:00Z",
            "displayFinancialStatus": "PAID",
            "displayFulfillmentStatus": "FULFILLED",
            "totalPriceSet": {"shopMoney": {"amount": "189.00", "currencyCode": "USD"}},
            "fulfillments": {"nodes": [{"deliveredAt": "2026-08-05T10:00:00Z"}]},
            "lineItems": {
                "nodes": [
                    {
                        "id": "gid://shopify/LineItem/11",
                        "name": "2-Person Tent",
                        "quantity": 1,
                        "sku": "TENT-2P",
                        "originalUnitPriceSet": {
                            "shopMoney": {"amount": "189.00", "currencyCode": "USD"}
                        },
                    }
                ]
            },
        }
    },
    "extensions": {"cost": {"requestedQueryCost": 12, "actualQueryCost": 9}},
}

RETURNABLE_RESPONSE = {
    "data": {
        "returnableFulfillments": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/ReturnableFulfillment/1",
                        "returnableFulfillmentLineItems": {
                            "edges": [
                                {
                                    "node": {
                                        "quantity": 1,
                                        "fulfillmentLineItem": {
                                            "id": "gid://shopify/FulfillmentLineItem/21",
                                            "lineItem": {"name": "2-Person Tent", "sku": "TENT-2P"},
                                        },
                                    }
                                }
                            ]
                        },
                    }
                }
            ]
        }
    }
}


def _admin(handler) -> ShopifyAdminClient:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ShopifyAdminClient("test.myshopify.com", "tok", client=client)


async def test_query_returns_data_and_records_cost() -> None:
    admin = _admin(lambda request: httpx.Response(200, json=ORDER_RESPONSE))
    data = await admin.query("query GetOrder($id: ID!) { order(id: $id) { id } }", {"id": "x"})
    assert data["order"]["name"] == "#1001"
    assert admin.last_cost == {"requestedQueryCost": 12, "actualQueryCost": 9}


async def test_http_error_raises() -> None:
    admin = _admin(lambda request: httpx.Response(401, text="Unauthorized"))
    with pytest.raises(ShopifyError, match="HTTP 401"):
        await admin.query("{ shop { name } }")


async def test_graphql_errors_raise() -> None:
    admin = _admin(
        lambda request: httpx.Response(200, json={"errors": [{"message": "Field not found"}]})
    )
    with pytest.raises(ShopifyError, match="GraphQL errors"):
        await admin.query("{ bogus }")


def test_empty_credentials_fail_loud() -> None:
    with pytest.raises(ValueError):
        ShopifyAdminClient("", "", client=None)  # type: ignore[arg-type]


async def test_get_order_maps_to_domain() -> None:
    backend = ShopifyPostPurchase(_admin(lambda request: httpx.Response(200, json=ORDER_RESPONSE)))
    order = await backend.get_order("gid://shopify/Order/1")
    assert order is not None
    assert (order.name, order.financial_status, order.fulfillment_status) == (
        "#1001",
        "PAID",
        "FULFILLED",
    )
    assert (order.total, order.currency) == (189.0, "USD")
    assert order.delivered_at == "2026-08-05T10:00:00Z"
    assert order.line_items == [
        LineItem(id="gid://shopify/LineItem/11", title="2-Person Tent", quantity=1, sku="TENT-2P")
    ]


async def test_get_order_in_transit_has_no_delivery_date() -> None:
    """A fulfilled order with no DELIVERED event has no delivery date (escalate)."""
    import copy

    payload = copy.deepcopy(ORDER_RESPONSE)
    payload["data"]["order"]["fulfillments"] = {"nodes": [{"deliveredAt": None}]}
    backend = ShopifyPostPurchase(_admin(lambda request: httpx.Response(200, json=payload)))
    order = await backend.get_order("gid://shopify/Order/1")
    assert order is not None
    assert order.delivered_at is None


async def test_get_order_unknown_returns_none() -> None:
    backend = ShopifyPostPurchase(
        _admin(lambda request: httpx.Response(200, json={"data": {"order": None}}))
    )
    assert await backend.get_order("gid://shopify/Order/404") is None


async def test_returnable_items_map() -> None:
    backend = ShopifyPostPurchase(
        _admin(lambda request: httpx.Response(200, json=RETURNABLE_RESPONSE))
    )
    items = await backend.returnable_items("gid://shopify/Order/1")
    assert items == [
        ReturnableItem(
            fulfillment_line_item_id="gid://shopify/FulfillmentLineItem/21",
            title="2-Person Tent",
            sku="TENT-2P",
            quantity=1,
        )
    ]


async def test_returnable_items_empty_when_none() -> None:
    backend = ShopifyPostPurchase(
        _admin(lambda request: httpx.Response(200, json={"data": {"returnableFulfillments": None}}))
    )
    assert await backend.returnable_items("gid://shopify/Order/1") == []


async def test_in_memory_backend_serves_the_contract() -> None:
    order = OrderView(
        id="gid://shopify/Order/1",
        name="#1001",
        created_at="2026-08-01T10:00:00Z",
        financial_status="PAID",
        fulfillment_status="FULFILLED",
        total=189.0,
        currency="USD",
    )
    backend = InMemoryPostPurchase(
        {order.id: order},
        {order.id: [ReturnableItem("gid://shopify/FulfillmentLineItem/21", "Tent", "TENT-2P", 1)]},
    )
    assert (await backend.get_order(order.id)) == order
    assert len(await backend.returnable_items(order.id)) == 1
    assert await backend.get_order("missing") is None


async def test_returnable_items_resolves_a_human_order_number() -> None:
    """The returnable query needs a global id; a human number must be resolved first.

    Passing "1006" straight through made Shopify reject the query
    ("Variable $id of type ID! was provided invalid value"), the tool fail, and the
    agent loop over id formats - the root cause of the return-case tool churn.
    """
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        seen.append(body)
        if "returnableFulfillments" in body["query"]:
            return httpx.Response(200, json=RETURNABLE_RESPONSE)
        # the by-name lookup returns orders.nodes, not order
        return httpx.Response(
            200, json={"data": {"orders": {"nodes": [ORDER_RESPONSE["data"]["order"]]}}}
        )

    backend = ShopifyPostPurchase(_admin(handler))
    items = await backend.returnable_items("1006")

    assert [item.fulfillment_line_item_id for item in items] == [
        "gid://shopify/FulfillmentLineItem/21"
    ]
    assert len(seen) == 2, "expected an order lookup followed by the returnable query"
    assert seen[0]["variables"]["q"] == "name:#1006"
    assert seen[1]["variables"]["id"] == "gid://shopify/Order/1", (
        "the returnable query must receive the resolved global id, not the human number"
    )


async def test_returnable_items_for_an_unknown_number_makes_no_second_call() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        body = json.loads(request.content)
        calls.append(body["query"])
        return httpx.Response(200, json={"data": {"orders": {"nodes": []}}})

    backend = ShopifyPostPurchase(_admin(handler))
    assert await backend.returnable_items("nope") == []
    assert len(calls) == 1
