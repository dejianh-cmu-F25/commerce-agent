"""Chroma-backed vector store (Service Provider for
:class:`app.ports.vector_store.VectorStore`).

Persistent, embedded Chroma collection with cosine space. The harness supplies
the embeddings, so Chroma's default embedding function is disabled and nothing is
downloaded; anonymized telemetry is off (keyless, P8). Upsert is keyed by chunk
id, so re-ingestion does not duplicate vectors (RD-2).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.filters import to_chroma_where
from app.core.types import Chunk

_SCALARS = (str, int, float, bool)


def _metadata(chunk: Chunk) -> dict[str, Any]:
    """Chroma metadata: JSON scalars only (no None, no nested values)."""
    data: dict[str, Any] = {"source": chunk.source}
    for key, value in chunk.metadata.items():
        if value is not None and isinstance(value, _SCALARS):
            data[key] = value
    return data


class ChromaVectorStore:
    def __init__(self, persist_directory: str, collection_name: str) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:  # pragma: no cover - only without the dependency
            raise RuntimeError(
                "vector_store.provider 'chroma' requires the 'chromadb' package"
            ) from exc

        self._path = Path(persist_directory)
        self._path.mkdir(parents=True, exist_ok=True)
        self._client: Any = chromadb.PersistentClient(
            path=str(self._path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection: Any = self._client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[_metadata(chunk) for chunk in chunks],
        )

    def size(self) -> int:
        return int(self._collection.count())

    def query(
        self, embedding: list[float], k: int = 3, where: dict[str, Any] | None = None
    ) -> list[Chunk]:
        count = self.size()
        if count == 0:
            return []
        chroma_where = to_chroma_where(where)
        arguments: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": min(max(1, k), count),
            "include": ["documents", "metadatas", "distances"],
        }
        if chroma_where is not None:
            arguments["where"] = chroma_where
        result = self._collection.query(**arguments)
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        hits: list[Chunk] = []
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances, strict=False
        ):
            score = 1.0 - float(distance)
            if score <= 0:
                continue
            fields = dict(metadata or {})
            hits.append(
                Chunk(
                    id=str(chunk_id),
                    text=str(document),
                    source=str(fields.get("source", "")),
                    score=round(score, 6),
                    metadata=fields,
                )
            )
        return hits
