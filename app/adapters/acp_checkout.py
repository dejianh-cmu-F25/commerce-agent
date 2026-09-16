"""Simulated, ACP-conformant checkout adapter (feature 046).

Implements the create → update → complete lifecycle without taking money: the
payment token is a placeholder and ``charge_issued`` is always ``False``. This is
the honest way to demonstrate agentic checkout in a portfolio project.
"""

from __future__ import annotations

from uuid import uuid4

from app.ports.checkout import (
    COMPLETED,
    CREATED,
    FAILED,
    READY,
    CheckoutSession,
)


class AcpCheckout:
    """An in-memory ACP-shaped checkout that never charges."""

    def __init__(self) -> None:
        self._sessions: dict[str, CheckoutSession] = {}

    def create_session(self, cart_id: str, total: float, currency: str = "USD") -> CheckoutSession:
        session = CheckoutSession(
            id=f"cs_{uuid4().hex[:12]}",
            cart_id=cart_id,
            status=CREATED,
            total=total,
            currency=currency,
        )
        self._sessions[session.id] = session
        return session

    def update_session(self, session_id: str, address: str) -> CheckoutSession:
        session = self._get(session_id)
        updated = CheckoutSession(
            id=session.id,
            cart_id=session.cart_id,
            status=READY,
            total=session.total,
            currency=session.currency,
            address=address,
        )
        self._sessions[session.id] = updated
        return updated

    def complete(self, session_id: str) -> CheckoutSession:
        session = self._get(session_id)
        if session.status != READY:
            failed = CheckoutSession(
                id=session.id,
                cart_id=session.cart_id,
                status=FAILED,
                total=session.total,
                currency=session.currency,
                address=session.address,
            )
            self._sessions[session.id] = failed
            return failed
        completed = CheckoutSession(
            id=session.id,
            cart_id=session.cart_id,
            status=COMPLETED,
            total=session.total,
            currency=session.currency,
            address=session.address,
            payment_token=f"sim_{uuid4().hex[:16]}",  # placeholder; no charge
            charge_issued=False,
        )
        self._sessions[session.id] = completed
        return completed

    def _get(self, session_id: str) -> CheckoutSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown checkout session: {session_id}")
        return session
