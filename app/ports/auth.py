"""Auth capability: Service Definition (constitution PB-2, feature 046).

Simulated for this project: a principal is resolved from a token; there is no
real OAuth. The gate (``app/gates/tenancy.py``) enforces isolation regardless of
how the principal was resolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Principal:
    customer_id: str
    name: str = ""


class AuthBackend(Protocol):
    def authenticate(self, token: str) -> Principal | None:
        """Return the principal for ``token``, or ``None`` if unknown."""
        ...
