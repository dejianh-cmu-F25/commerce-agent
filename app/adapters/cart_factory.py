"""Resolve the cart backend from configuration (PB-1: config as contract).

Lives in ``app/`` rather than next to the web app so that every surface that wires the
cart tools - the in-process agent *and* the MCP servers - resolves the same provider from
the same config. A surface that picked its own backend would make ``cart.provider`` a
half-truth.
"""

from __future__ import annotations

from typing import Any

from app.core.settings import Settings


def build_cart(settings: Settings) -> Any:
    """Return the configured cart backend.

    The Storefront provider needs its own token and fails loud without one, because a
    deployment that asked for a real cart must not silently get a session cart.
    """
    if settings.cart.provider == "shopify_storefront":
        from app.adapters.cart_shopify import ShopifyStorefrontCart

        return ShopifyStorefrontCart(
            settings.shopify.shop,
            settings.shopify.storefront_token,
            settings.shopify.api_version,
        )
    from app.adapters.cart_session import SessionCart

    return SessionCart()
