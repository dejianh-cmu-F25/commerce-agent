"""Query understanding: turn a shopper's request into a retrieval plan (047).

A **need query** names a task or situation, not a product; the words that match
live in the product's review/feature text, and the query may also carry hard
constraints ("under $30"). This port is the replaceable step that rewrites the
request into retrieval terms and extracts filters.

Two providers: a deterministic keyless one (`app/adapters/query_rules.py`) and an
opt-in LLM one (HyDE-style, `app/adapters/query_llm.py`), selected by
``catalog.query_understanding`` (PB-1). The deterministic path is the fallback
when the model is unavailable (RD-1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class QueryPlan:
    """What to retrieve: the (possibly rewritten) terms and a metadata filter."""

    terms: str
    where: dict[str, Any] = field(default_factory=dict)
    note: str = ""


class QueryUnderstanding(Protocol):
    name: str

    async def understand(self, query: str) -> QueryPlan:
        """Return the retrieval plan for ``query``; never raise on bad input."""
        ...
