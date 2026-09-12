"""In-memory customer memory provider (Service Provider for
:class:`app.ports.memory.MemoryStore`).

Keyless, for the demo path and tests. Facts are unique per
``(customer_id, kind, text)`` (RD-2).
"""

from __future__ import annotations

from app.core.types import MemoryFact


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._facts: list[MemoryFact] = []
        self._keys: set[tuple[str, str, str]] = set()

    @staticmethod
    def _key(fact: MemoryFact) -> tuple[str, str, str]:
        return (fact.customer_id, fact.kind, fact.text)

    def add(self, fact: MemoryFact) -> bool:
        key = self._key(fact)
        if key in self._keys:
            return False
        self._keys.add(key)
        self._facts.append(fact)
        return True

    def list(self, customer_id: str, limit: int = 50) -> list[MemoryFact]:
        items = [fact for fact in self._facts if fact.customer_id == customer_id]
        return items[: max(1, limit)]

    def forget(self, customer_id: str, fact_id: str) -> bool:
        for index, fact in enumerate(self._facts):
            if fact.customer_id == customer_id and fact.id == fact_id:
                self._facts.pop(index)
                self._keys.discard(self._key(fact))
                return True
        return False

    def forget_all(self, customer_id: str) -> int:
        keep = [fact for fact in self._facts if fact.customer_id != customer_id]
        removed = len(self._facts) - len(keep)
        self._facts = keep
        self._keys = {self._key(fact) for fact in keep}
        return removed
