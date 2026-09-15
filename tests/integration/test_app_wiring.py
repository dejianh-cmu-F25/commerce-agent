"""Provider selection in `web/main.py:build_agent` (PB-1)."""

import pytest


def test_the_shopify_cart_provider_fails_loud_without_a_token() -> None:
    """A deployment that asks for a real cart must not silently get a session cart."""
    from app.core.settings import CartSettings, Settings
    from web.main import build_cart

    settings = Settings(cart=CartSettings(provider="shopify_storefront"))
    with pytest.raises(ValueError, match="STOREFRONT_TOKEN"):
        build_cart(settings)


def test_the_default_cart_backend_is_the_session_one() -> None:
    from app.adapters.cart_session import SessionCart
    from app.core.settings import Settings
    from web.main import build_cart

    assert isinstance(build_cart(Settings()), SessionCart)


def test_the_mcp_servers_resolve_the_same_cart_provider() -> None:
    """`cart.provider` must not be a half-truth: the MCP surface honours it too.

    A Storefront cart without a token has to fail here exactly as it does in the web app,
    which is only true if the MCP builders go through the same factory.
    """
    from app.core.settings import CartSettings, Settings
    from app.mcp.server import build_checkout_server, build_storefront_server

    settings = Settings(cart=CartSettings(provider="shopify_storefront"))
    for builder in (build_storefront_server, build_checkout_server):
        with pytest.raises(ValueError, match="STOREFRONT_TOKEN"):
            builder(settings)


def test_the_mcp_servers_build_with_the_default_session_cart() -> None:
    from app.core.settings import Settings
    from app.mcp.server import build_checkout_server, build_storefront_server

    assert build_storefront_server(Settings()) is not None
    assert build_checkout_server(Settings()) is not None
