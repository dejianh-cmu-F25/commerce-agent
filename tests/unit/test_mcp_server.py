"""MCP servers expose the journey tools (feature 046, FR-016)."""

from __future__ import annotations

import asyncio

from mcp.server.mcpserver import MCPServer

from app.mcp.server import (
    build_checkout_server,
    build_customer_accounts_server,
    build_storefront_server,
)


def _names(server: MCPServer) -> list[str]:
    return sorted(tool.name for tool in asyncio.run(server.list_tools()))


def test_storefront_tools() -> None:
    assert _names(build_storefront_server()) == [
        "add_to_cart",
        "render_checkout",
        "search_knowledge",
        "search_products",
        "view_cart",
    ]


def test_customer_accounts_tools() -> None:
    assert _names(build_customer_accounts_server()) == [
        "get_order_status",
        "list_orders",
        "list_returnable_items",
        "propose_return_decision",
    ]


def test_checkout_tools() -> None:
    assert _names(build_checkout_server()) == ["add_to_cart", "render_checkout", "view_cart"]


def test_tool_call_returns_content() -> None:
    server = build_storefront_server()
    result = asyncio.run(server.call_tool("search_products", {"query": "tent"}))
    text = str(result)
    assert "P-101" in text or "Tent" in text
