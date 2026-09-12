"""OpenAI-compatible embedding provider (Service Provider for
:class:`app.ports.embedding.EmbeddingProvider`).

Opt-in: needs an API key. Uses the existing ``openai`` dependency and the
configured base URL, so it works with any OpenAI-compatible endpoint. A client
can be injected for tests.
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI


class OpenAIEmbeddingProvider:
    def __init__(
        self,
        *,
        model: str,
        api_key: str = "",
        base_url: str = "",
        client: Any | None = None,
    ) -> None:
        self._model = model
        self._client = client or OpenAI(api_key=api_key or "not-set", base_url=base_url or None)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [list(item.embedding) for item in response.data]
