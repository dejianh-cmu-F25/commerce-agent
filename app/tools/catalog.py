"""A tiny in-memory catalog and the ``search_products`` tool.

This is a stand-in for the real catalog backend; feature 002 replaces it with a
proper StorefrontBackend. It exists here to prove the loop can call a tool and
to exercise provenance (only server-issued product ids are remembered).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.tools.registry import ToolRegistry, ToolResult

_CATALOG: list[dict[str, Any]] = [
    {
        "id": "P-101",
        "title": "2-Person Tent",
        "price": 189.0,
        "stock": 12,
        "tags": ["camping", "tent"],
    },
    {
        "id": "P-102",
        "title": "Down Sleeping Bag",
        "price": 129.0,
        "stock": 7,
        "tags": ["camping", "sleep"],
    },
    {"id": "P-103", "title": "Camp Stove", "price": 64.0, "stock": 0, "tags": ["camping", "cook"]},
    {
        "id": "P-104",
        "title": "Trail Backpack 40L",
        "price": 95.0,
        "stock": 20,
        "tags": ["camping", "hike"],
    },
    {
        "id": "P-105",
        "title": "Insulated Water Bottle",
        "price": 24.0,
        "stock": 50,
        "tags": ["camping", "drink"],
    },
]

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


def _matches(query: str) -> list[dict[str, Any]]:
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in _CATALOG:
        haystack = f"{item['title']} {' '.join(item['tags'])}".lower()
        score = sum(1 for t in terms if t in haystack)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [item for _, item in scored]


async def _search_products(arguments: dict[str, Any], session: Session) -> ToolResult:
    query = str(arguments.get("query", "")).strip()
    limit = int(arguments.get("limit", 5))
    results = _matches(query)[:limit]

    session.remember_ids([item["id"] for item in results])

    if not results:
        return ToolResult(content=json.dumps({"query": query, "results": []}))

    payload = {
        "query": query,
        "results": [
            {"id": i["id"], "title": i["title"], "price": i["price"], "in_stock": i["stock"] > 0}
            for i in results
        ],
    }
    return ToolResult(content=json.dumps(payload))


def register_catalog_tools(registry: ToolRegistry) -> None:
    registry.register(SEARCH_PRODUCTS_SPEC, _search_products)
