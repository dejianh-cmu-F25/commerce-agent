"""Load markdown knowledge documents into paragraph chunks (P4, RD-2).

Chunk ids are ``"{source}#{index}"`` (stable), so re-ingestion is idempotent.
A missing directory yields no chunks rather than an error.
"""

from __future__ import annotations

from pathlib import Path

from app.core.types import Chunk


def load_chunks(path: str, min_chars: int = 40) -> list[Chunk]:
    root = Path(path)
    if not root.exists():
        return []

    chunks: list[Chunk] = []
    for file in sorted(root.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        for index, block in enumerate(text.split("\n\n")):
            paragraph = " ".join(block.split())
            if len(paragraph) < min_chars:
                continue
            chunks.append(Chunk(id=f"{file.name}#{index}", text=paragraph, source=file.name))
    return chunks
