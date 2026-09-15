"""MCP servers exposing the journey tools (feature 046, FR-016).

Each server exposes a group of the agent's tools over the Model Context Protocol
so any MCP client can consume them. The harness remains the only executor: the
servers wrap the same :class:`ToolRegistry` used in-process, so the policy gate
and invariants still apply.

Run one with::

    python -m app.mcp.server --server storefront --transport stdio
"""

from __future__ import annotations

import argparse
import inspect
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from mcp.server.mcpserver import MCPServer

from app.adapters.cart_factory import build_cart
from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.post_purchase_memory import InMemoryPostPurchase
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.storefront_memory import InMemoryStorefront
from app.core.session import Session
from app.core.settings import Settings, load_settings
from app.knowledge.ingest import load_chunks
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.knowledge import register_knowledge_tools
from app.tools.post_purchase import register_post_purchase_tools
from app.tools.registry import ToolRegistry

KNOWLEDGE_PATH = "config/knowledge"

_JSON_TO_PY: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _signature(spec: Any) -> inspect.Signature:
    """Build a Python signature from the tool's JSON schema so MCP can introspect it."""
    properties = spec.parameters.get("properties", {})
    required = set(spec.parameters.get("required", []))
    params: list[inspect.Parameter] = []
    for param_name, schema in properties.items():
        annotation = _JSON_TO_PY.get(schema.get("type", "string"), str)
        if param_name in required:
            params.append(
                inspect.Parameter(param_name, inspect.Parameter.KEYWORD_ONLY, annotation=annotation)
            )
        else:
            params.append(
                inspect.Parameter(
                    param_name,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=None,
                    annotation=annotation | None,  # type: ignore[operator]
                )
            )
    return inspect.Signature(params)


def build_server(name: str, registry: ToolRegistry, *, instructions: str = "") -> MCPServer:
    """Expose every tool in ``registry`` over MCP."""
    server = MCPServer(name, instructions=instructions or None)
    for spec in registry.specs():
        server.add_tool(_wrap(registry, spec), name=spec.name, description=spec.description)
    return server


def _wrap(registry: ToolRegistry, spec: Any) -> Callable[..., object]:
    async def tool(**kwargs: object) -> str:
        session = Session(id=f"mcp-{uuid4().hex[:8]}")
        # Drop unset optionals so the tool's own defaults apply.
        arguments = {key: value for key, value in kwargs.items() if value is not None}
        result = await registry.execute(spec.name, arguments, session)
        return result.content

    tool.__name__ = spec.name
    tool.__signature__ = _signature(spec)  # type: ignore[attr-defined]
    return tool


def _retriever() -> InMemoryRetriever:
    retriever = InMemoryRetriever()
    retriever.add(load_chunks(KNOWLEDGE_PATH))
    return retriever


def build_storefront_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or load_settings()
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront, build_cart(settings))
    register_knowledge_tools(registry, _retriever())
    return build_server(
        "storefront", registry, instructions="Catalog search, cart, and store policy."
    )


def build_customer_accounts_server() -> MCPServer:
    registry = ToolRegistry()
    register_post_purchase_tools(registry, InMemoryPostPurchase({}))
    return build_server("customer-accounts", registry, instructions="Orders and returns.")


def build_checkout_server(settings: Settings | None = None) -> MCPServer:
    settings = settings or load_settings()
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_cart_tools(registry, storefront, build_cart(settings))
    return build_server("checkout", registry, instructions="Checkout (simulated; no charge).")


SERVERS: dict[str, Callable[[], MCPServer]] = {
    "storefront": build_storefront_server,
    "customer-accounts": build_customer_accounts_server,
    "checkout": build_checkout_server,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an MCP server for the shopping agent.")
    parser.add_argument("--server", choices=sorted(SERVERS), default="storefront")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio")
    args = parser.parse_args()
    SERVERS[args.server]().run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
