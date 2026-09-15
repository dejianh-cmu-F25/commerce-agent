"""Session-backed cart (Service Provider for :class:`app.ports.cart.CartBackend`).

The keyless default, and the behaviour the cart always had: lines live on the session,
so they persist with it (feature 005) and the transcript can re-render them.
"""

from __future__ import annotations

from app.core.session import CartLine, Session
from app.core.types import Product


class SessionCart:
    def add(self, session: Session, product: Product, quantity: int) -> None:
        line = next((item for item in session.cart if item.product_id == product.id), None)
        if line is None:
            session.cart.append(
                CartLine(
                    product_id=product.id,
                    title=product.title,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )
            return
        line.quantity += quantity

    def view(self, session: Session) -> list[CartLine]:
        return list(session.cart)
