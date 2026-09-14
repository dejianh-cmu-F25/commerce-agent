"""Checkout capability: Service Definition (constitution PB-2, feature 046).

A checkout session follows the Agentic Commerce Protocol shape: create → update →
complete. The harness owns completion (HITL); an adapter never charges on its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

CREATED = "created"
READY = "ready"
COMPLETED = "completed"
FAILED = "failed"


@dataclass(frozen=True)
class CheckoutSession:
    id: str
    cart_id: str
    status: str
    total: float
    currency: str = "USD"
    payment_token: str | None = None
    address: str | None = None
    charge_issued: bool = False


class CheckoutBackend(Protocol):
    def create_session(self, cart_id: str, total: float, currency: str = "USD") -> CheckoutSession:
        """Open a checkout session for a cart."""
        ...

    def update_session(self, session_id: str, address: str) -> CheckoutSession:
        """Attach buyer details; move the session to ``ready``."""
        ...

    def complete(self, session_id: str) -> CheckoutSession:
        """Complete the session (simulated). Must not charge in this project."""
        ...
