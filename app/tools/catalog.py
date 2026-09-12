"""The ``search_products`` tool, backed by an injected storefront.

The tool is a consumer of :class:`app.ports.storefront.StorefrontBackend`
(PB-2). It reads products from the backend and remembers only the ids the
backend returned (grounding, P4).
"""

from __future__ import annotations

import json
from typing import Any

from app.adapters.storefront_common import clamp_limit
from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.storefront import StorefrontBackend
from app.tools.registry import ToolRegistry, ToolResult

SEARCH_PRODUCTS_SPEC = ToolSpec(
    name="search_products",
    description=(
        "Search the store catalog for products matching a natural-language query. "
        "Returns a ranked shortlist. Use this for any product request."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What the customer is looking for."},
            "limit": {
                "type": "integer",
                "description": "Max results (default 5).",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": ["query"],
    },
)


def _items(results: list[Any]) -> list[dict[str, Any]]:
    return [
        {"id": p.id, "title": p.title, "price": p.price, "in_stock": p.in_stock} for p in results
    ]


def register_catalog_tools(registry: ToolRegistry, storefront: StorefrontBackend) -> None:
    async def _search_products(arguments: dict[str, Any], session: Session) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        limit = clamp_limit(int(arguments.get("limit", 5)))
        results = storefront.search(query, limit)
        session.remember_ids([p.id for p in results])

        if not results:
            return ToolResult(content=json.dumps({"query": query, "results": []}))

        items = _items(results)
        return ToolResult(
            content=json.dumps({"query": query, "results": items}),
            component="products",
            payload={"items": items},
        )

    registry.register(SEARCH_PRODUCTS_SPEC, _search_products)
