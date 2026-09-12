"""Embedding capability: Service Definition (constitution PB-2).

Turns text into fixed-dimension vectors for dense retrieval. Providers live in
``app/adapters`` and are selected by configuration (PB-1). The keyless provider
is the default (P8); a real provider is opt-in.
"""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order.

        An empty input returns ``[]``. Vectors need not be normalized.
        """
        ...
