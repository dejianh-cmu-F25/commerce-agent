"""Unit tests for the keyless hashing embedding (feature 018)."""

from __future__ import annotations

import math

from app.adapters.embedding_hash import HashEmbeddingProvider


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def test_is_deterministic_and_has_dimensions():
    embedding = HashEmbeddingProvider(64)
    first = embedding.embed(["I prefer lightweight tents"])[0]
    second = embedding.embed(["I prefer lightweight tents"])[0]
    assert first == second
    assert len(first) == 64
    assert embedding.embed([]) == []


def test_similar_texts_are_closer_than_unrelated():
    embedding = HashEmbeddingProvider(256)
    query, near, far = embedding.embed(
        ["return policy refund", "return policy refund window", "carrier delivery shipping"]
    )
    assert _cosine(query, near) > _cosine(query, far)
