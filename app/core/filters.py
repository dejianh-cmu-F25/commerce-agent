"""Metadata filters for retrieval (feature 047).

A ``where`` clause is a mapping of metadata field -> condition. A condition is
either a bare scalar (exact match) or a dict of operators:

    {"source": "review"}                       # equality
    {"source": "review", "rating": {"$gte": 4}}  # equality + range
    {"category": {"$in": ["All Beauty", "Books"]}}

The operators are the same names a vector store uses (Chroma/Mongo style:
``$eq``, ``$ne``, ``$in``, ``$gt``, ``$gte``, ``$lt``, ``$lte``), so the in-memory
stores and Chroma agree. A missing field never matches a comparison.
"""

from __future__ import annotations

from typing import Any

_COMPARISONS = ("$gt", "$gte", "$lt", "$lte")


def _cmp(value: Any, op: str, target: Any) -> bool:
    if value is None or target is None:
        return False
    try:
        if op == "$gt":
            return value > target
        if op == "$gte":
            return value >= target
        if op == "$lt":
            return value < target
        if op == "$lte":
            return value <= target
    except TypeError:
        return False
    return False


def metadata_matches(metadata: dict[str, Any], where: dict[str, Any] | None) -> bool:
    """True when ``metadata`` satisfies every condition in ``where``."""
    if not where:
        return True
    for field, condition in where.items():
        value = metadata.get(field)
        if isinstance(condition, dict):
            for op, target in condition.items():
                if op == "$eq":
                    if value != target:
                        return False
                elif op == "$ne":
                    if value == target:
                        return False
                elif op == "$in":
                    if value not in target:
                        return False
                elif op in _COMPARISONS:
                    if not _cmp(value, op, target):
                        return False
                else:
                    raise ValueError(f"unknown filter operator: {op!r}")
        elif value != condition:
            return False
    return True


def to_chroma_where(where: dict[str, Any] | None) -> dict[str, Any] | None:
    """Translate a ``where`` clause into Chroma's filter syntax."""
    if not where:
        return None
    clauses: list[dict[str, Any]] = []
    for field, condition in where.items():
        if isinstance(condition, dict):
            clauses.append({field: dict(condition)})
        else:
            clauses.append({field: {"$eq": condition}})
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}
