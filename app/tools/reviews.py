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


def register_review_tools(registry: ToolRegistry, reviews: ReviewBackend) -> None:
    async def _get_reviews(arguments: dict[str, Any], _session: Session) -> ToolResult:
        product_id = str(arguments.get("product_id", "")).strip()
        if not product_id:
            return ToolResult(content="product_id is required", status="error")
        limit = int(arguments.get("limit", 5))
        found = reviews.get_reviews(product_id, limit)
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
