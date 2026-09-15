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
