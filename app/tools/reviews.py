"""Review tools (feature 046).

``get_reviews`` returns real customer reviews for a product so the model can answer
"what do customers say" without inventing anything. Read-only.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.reviews import ReviewBackend
from app.tools.registry import ToolRegistry, ToolResult

GET_REVIEWS_SPEC = ToolSpec(
    name="get_reviews",
    description=(
        "Get real customer reviews for a product (most helpful first). Use this to "
        "answer 'what do customers say' or to weigh a recommendation. Read-only."
    ),
    parameters={
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "The product id / SKU."},
            "limit": {"type": "integer", "description": "Max reviews (default 5).", "minimum": 1},
        },
        "required": ["product_id"],
    },
)


def review_key(product_id: str, catalog: Any | None) -> str:
    """The key the review store uses for a product.

    Reviews come from Amazon Reviews'23 and are keyed by ASIN; the catalog carries
    that ASIN as the product's SKU. Resolving it here means the model can pass the id
    it was given by search_products - asking it to copy a second, opaque id is how the
    return flow ended up looping (feature 046). An unresolvable id is passed through
    unchanged, so fixtures and ASIN-keyed stores keep working.
    """
    if catalog is None or not product_id:
        return product_id
    try:
        product = catalog.get(product_id)
    except Exception:
        return product_id
    sku = str(getattr(product, "sku", "") or "")
    return sku or product_id


def register_review_tools(
    registry: ToolRegistry, reviews: ReviewBackend, catalog: Any | None = None
) -> None:
    async def _get_reviews(arguments: dict[str, Any], _session: Session) -> ToolResult:
        product_id = str(arguments.get("product_id", "")).strip()
        if not product_id:
            return ToolResult(content="product_id is required", status="error")
        limit = int(arguments.get("limit", 5))
        found = reviews.get_reviews(review_key(product_id, catalog), limit)
        if not found:
            return ToolResult(content=json.dumps({"product_id": product_id, "reviews": []}))
        payload = [
            {
                "rating": review.rating,
                "title": review.title,
                "text": review.text,
                "helpful_votes": review.helpful_votes,
                "verified": review.verified,
            }
            for review in found
        ]
        return ToolResult(
            content=json.dumps({"product_id": product_id, "reviews": payload}),
            component="reviews",
            payload={"items": payload},
        )

    registry.register(GET_REVIEWS_SPEC, _get_reviews)
