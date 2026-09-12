"""Merchant tools (agent-facing): list inventory and propose changes.

There is deliberately **no** approval tool: the model may propose, but only a
human applies a change (P3, "model proposes, harness disposes"). Approvals happen
through the web (`POST /merchant/changes/{id}/apply`).
"""

from __future__ import annotations

from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.merchant import MerchantBackend
from app.tools.registry import ToolRegistry, ToolResult

LIST_INVENTORY_SPEC = ToolSpec(
    name="list_inventory",
    description="List the catalog with prices and stock (operator view).",
    parameters={
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "description": "Max rows."}
        },
    },
)

PROPOSE_PRICE_SPEC = ToolSpec(
    name="propose_price_change",
    description=(
        "Propose a new price for a product. The change is staged and applied only "
        "after a human approves it in the merchant view."
    ),
    parameters={
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "The product id (e.g. P-101)."},
            "price": {"type": "number", "description": "The proposed price (> 0)."},
        },
        "required": ["product_id", "price"],
    },
)

PROPOSE_STOCK_SPEC = ToolSpec(
    name="propose_stock_change",
    description=(
        "Propose a new stock level for a product. Staged; applied only after human approval."
    ),
    parameters={
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "stock": {"type": "integer", "minimum": 0},
        },
        "required": ["product_id", "stock"],
    },
)

LIST_CHANGES_SPEC = ToolSpec(
    name="list_pending_changes",
    description="List the merchant changes awaiting approval.",
    parameters={"type": "object", "properties": {}},
)


def register_merchant_tools(registry: ToolRegistry, merchant: MerchantBackend) -> None:
    async def _list_inventory(arguments: dict[str, Any], _session: Session) -> ToolResult:
        limit = int(arguments.get("limit", 100))
        lines = [
            f"{p.id}  {p.title} — ${p.price:.2f}, stock {p.stock}"
            for p in merchant.list_products(limit)
        ]
        return ToolResult(content="Inventory:\n" + "\n".join(lines))

    async def _propose_price_change(arguments: dict[str, Any], _session: Session) -> ToolResult:
        try:
            change = merchant.stage_change(
                str(arguments.get("product_id", "")).strip(),
                "price",
                float(arguments.get("price", 0)),
            )
        except (ValueError, TypeError) as exc:
            return ToolResult(content=f"Could not stage the change: {exc}", status="error")
        return ToolResult(
            content=(
                f"Staged (pending approval): {change.product_id} price "
                f"${change.old_value:.2f} → ${change.new_value:.2f}. "
                "Approve it in the Merchant view."
            )
        )

    async def _propose_stock_change(arguments: dict[str, Any], _session: Session) -> ToolResult:
        try:
            change = merchant.stage_change(
                str(arguments.get("product_id", "")).strip(),
                "stock",
                float(arguments.get("stock", 0)),
            )
        except (ValueError, TypeError) as exc:
            return ToolResult(content=f"Could not stage the change: {exc}", status="error")
        return ToolResult(
            content=(
                f"Staged (pending approval): {change.product_id} stock "
                f"{change.old_value:.0f} → {change.new_value:.0f}. "
                "Approve it in the Merchant view."
            )
        )

    async def _list_pending_changes(_arguments: dict[str, Any], _session: Session) -> ToolResult:
        changes = merchant.pending()
        if not changes:
            return ToolResult(content="No pending changes.")
        lines = [
            f"{c.id}  {c.product_id}  {c.kind} {c.old_value:.2f} → {c.new_value:.2f}"
            for c in changes
        ]
        return ToolResult(content="Pending changes:\n" + "\n".join(lines))

    registry.register(LIST_INVENTORY_SPEC, _list_inventory)
    registry.register(PROPOSE_PRICE_SPEC, _propose_price_change)
    registry.register(PROPOSE_STOCK_SPEC, _propose_stock_change)
    registry.register(LIST_CHANGES_SPEC, _list_pending_changes)
