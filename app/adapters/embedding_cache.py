"""Embedding cache (Service Provider decorator, feature 046).

Wraps any :class:`~app.ports.embedding.EmbeddingProvider` with a SQLite cache keyed
by the text, so evaluation re-runs do not pay for embeddings twice. Batches the
misses because providers cap the number of inputs per request.

The cache lives under ``data/`` (gitignored).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from app.ports.embedding import EmbeddingProvider

_SCHEMA = """
CREATE TABLE IF NOT EXISTS embeddings (
    key TEXT PRIMARY KEY,
    vector TEXT NOT NULL
);
"""


class CachedEmbeddingProvider:
    def __init__(
        self,
        provider: EmbeddingProvider,
        path: str | Path,
        *,
        batch_size: int = 100,
    ) -> None:
        self._provider = provider
        self._path = str(path)
        self._batch = max(1, batch_size)
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._path) as conn:
            conn.executescript(_SCHEMA)

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load(self, keys: list[str]) -> dict[str, list[float]]:
        found: dict[str, list[float]] = {}
        with sqlite3.connect(self._path) as conn:
            for start in range(0, len(keys), 500):
                chunk = keys[start : start + 500]
                placeholders = ",".join("?" for _ in chunk)
                rows = conn.execute(
                    f"SELECT key, vector FROM embeddings WHERE key IN ({placeholders})", chunk
                ).fetchall()
                for key, vector in rows:
                    found[key] = json.loads(vector)
        return found

    def _store(self, items: dict[str, list[float]]) -> None:
        if not items:
            return
        with sqlite3.connect(self._path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO embeddings (key, vector) VALUES (?, ?)",
                [(key, json.dumps(vector)) for key, vector in items.items()],
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        keys = [self._key(text) for text in texts]
        cache = self._load(keys)
        misses = [text for text, key in zip(texts, keys, strict=True) if key not in cache]
        unique_misses = list(dict.fromkeys(misses))
        for start in range(0, len(unique_misses), self._batch):
            batch = unique_misses[start : start + self._batch]
            vectors = self._provider.embed(batch)
            stored = {self._key(text): vector for text, vector in zip(batch, vectors, strict=True)}
            self._store(stored)
            cache.update(stored)
        return [cache[key] for key in keys]
