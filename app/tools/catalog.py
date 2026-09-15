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
from app.core.types import Product, ToolSpec
from app.ports.storefront import StorefrontBackend
from app.tools.registry import ToolRegistry, ToolResult

SEARCH_PRODUCTS_SPEC = ToolSpec(
    name="search_products",
    description=(
        "Search the store catalog for products matching a natural-language query. "
        "Returns a ranked shortlist. Use this for any product request. Pass the "
        "customer's explicit constraints (a maximum price, a category) as arguments: "
        "the store applies them exactly, so never widen them yourself."
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
            "max_price": {
                "type": "number",
                "description": (
                    "Only return products at or below this price (the customer's budget)."
                ),
            },
            "category": {
                "type": "string",
                "description": "Only return products in this category.",
            },
            "in_stock_only": {
                "type": "boolean",
                "description": "Only return products that are in stock.",
            },
        },
        "required": ["query"],
    },
)

# Candidates pulled before an explicit constraint is applied, so filtering has
# something to keep. The constraint is enforced by the harness, never the model.
OVERFETCH = 5


def _matches_category(product: Product, category: str) -> bool:
    """Match the category against the product's tags (Shopify stores them with spaces)."""
    wanted = " ".join(category.replace("_", " ").casefold().split())
    if not wanted:
        return True
    for tag in product.tags:
        text = " ".join(tag.replace("_", " ").casefold().split())
        if text == wanted or text == f"category: {wanted}" or wanted in text or text in wanted:
            return True
    return False


def _items(results: list[Any]) -> list[dict[str, Any]]:
    return [
        {"id": p.id, "title": p.title, "price": p.price, "in_stock": p.in_stock} for p in results
    ]


def register_catalog_tools(
    registry: ToolRegistry,
    storefront: StorefrontBackend,
    reranker: Any | None = None,
) -> None:
    async def _search_products(arguments: dict[str, Any], session: Session) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        limit = clamp_limit(int(arguments.get("limit", 5)))
        max_price = arguments.get("max_price")
        category = str(arguments.get("category", "") or "").strip()
        in_stock_only = bool(arguments.get("in_stock_only", False))
        constrained = max_price is not None or bool(category) or in_stock_only

        results = storefront.search(query, clamp_limit(limit * OVERFETCH) if constrained else limit)
        if max_price is not None:
            results = [p for p in results if p.price <= float(max_price)]
        if category:
            results = [p for p in results if _matches_category(p, category)]
        if in_stock_only:
            # Stock comes from the live product, never the index (step A2).
            results = [p for p in results if p.in_stock]
        if reranker is not None and len(results) > 1:
            # Second stage: reorder the eligible candidates by relevance (A6). The
            # reranker falls back to this order if it fails, so search never breaks.
            results = await reranker.rerank(query, results, limit)
        else:
            results = results[:limit]
        session.remember_ids([p.id for p in results])

        payload: dict[str, Any] = {"query": query, "results": _items(results)}
        if constrained:
            # Report what was enforced, so the answer can be honest about an empty
            # result instead of quietly ignoring the customer's constraint.
            payload["constraints"] = {
                "max_price": float(max_price) if max_price is not None else None,
                "category": category or None,
                "in_stock_only": in_stock_only,
            }
        return ToolResult(
            content=json.dumps(payload),
            component="products",
            payload={"items": payload["results"]},
        )

    registry.register(SEARCH_PRODUCTS_SPEC, _search_products)
