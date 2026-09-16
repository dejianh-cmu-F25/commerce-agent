"""Deterministic, keyless query understanding (feature 047).

The safe default: it does not rewrite the terms (a rules engine guessing
synonyms would be overfitting), but it **extracts hard constraints** a shopper
states explicitly into a metadata filter. That is the part a rule can do
honestly, and it is the fallback when no model is available (RD-1).

Scope is deliberately narrow: a **price ceiling** only. An earlier version also
guessed a category from trailing "in X", which false-positived on "healthy in
summer" and *lowered* need hit@10 to 0.708 - a rule that reads intent is a rule
that will be wrong, so it extracts only the constraint whose grammar is
unambiguous.
"""

from __future__ import annotations

import re

from app.ports.query_understanding import QueryPlan

_PRICE = re.compile(
    r"(?:under|below|less than|cheaper than|at most|up to|max(?:imum)?)\s*\$?(\d+(?:\.\d+)?)",
    re.I,
)


class RuleQueryUnderstanding:
    name = "rules"

    async def understand(self, query: str) -> QueryPlan:
        where: dict = {}
        price = _PRICE.search(query or "")
        if price:
            where["price"] = {"$lte": float(price.group(1))}
        return QueryPlan(terms=query, where=where, note="rule-based constraints")
