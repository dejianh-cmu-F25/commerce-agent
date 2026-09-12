"""Keyless hashing embedding (Service Provider for
:class:`app.ports.embedding.EmbeddingProvider`).

Feature hashing over whitespace tokens: deterministic, dependency-free, and
requires no provider (P8). It is lexical rather than semantic; the OpenAI
provider is the opt-in upgrade.
"""

from __future__ import annotations

import hashlib
import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = max(8, dimensions)

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]
