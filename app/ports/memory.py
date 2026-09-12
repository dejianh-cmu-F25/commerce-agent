"""Customer memory capability: Service Definition (constitution PB-2).

Cross-session facts about a customer: preferences, constraints, and profile.
Facts are grounded in what the customer said (P4) and are read-only model
context. The harness owns writes; the model never writes memory (P3). Providers
live in ``app/adapters`` and are selected by configuration (PB-1).
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import MemoryFact


class MemoryStore(Protocol):
    def add(self, fact: MemoryFact) -> bool:
        """Store a fact. Return ``False`` if an equal fact already exists (RD-2)."""
        ...

    def list(self, customer_id: str, limit: int = 50) -> list[MemoryFact]:
        """Return the customer's facts, oldest first."""
        ...

    def forget(self, customer_id: str, fact_id: str) -> bool:
        """Remove one fact. Return ``False`` if it is unknown."""
        ...

    def forget_all(self, customer_id: str) -> int:
        """Remove all facts for a customer; return the number removed."""
        ...
