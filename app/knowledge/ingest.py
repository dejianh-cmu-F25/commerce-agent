"""Load markdown knowledge documents into **section** chunks (P4, RD-2).

A clause and its heading belong together: the heading is the clause's identity
(``returns#window-default``) and the body is the rule it states. The previous loader
split on blank lines and dropped any block shorter than ``min_chars`` — which is
every heading — so a retrieved rule arrived with no name attached and the model had
to guess one (in a traced run it invented ``returns.md``). Each chunk now carries its
heading as its first words, which keeps the clause id both **visible to the model**
and **searchable** without adding a field every retriever and vector store would then
have to copy around.

Chunk ids are ``"{source}#{index}"`` (stable), so re-ingestion is idempotent.
A missing directory yields no chunks rather than an error.
"""

from __future__ import annotations

from pathlib import Path

from app.core.types import Chunk


def _sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs, one per ``#`` heading.

    Text before the first heading is its own section with an empty heading. The body
    keeps its **original lines**: flattening it first would collapse a whole section
    into one line and make any per-line test — such as the provenance check — read the
    section's first character (that bug silently deleted the entire shipping document).
    """
    sections: list[tuple[str, str]] = []
    heading = ""
    body: list[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            sections.append((heading, "\n".join(body)))
            heading = line.lstrip("#").strip()
            body = []
        else:
            body.append(line)
    sections.append((heading, "\n".join(body)))
    return sections


def _flatten(text: str) -> str:
    return " ".join(text.split())


_PROVENANCE_PREFIXES = (">", "source:")


def _strip_provenance(body: str) -> str:
    """Drop provenance and scope-note lines (``>`` quotes, ``Source:``) from a body.

    They are not policy content, and leaving them in has a measurable cost: the
    shipping document carries the note "it is not part of the **return-decision
    policy**", which made it outrank every returns clause for the query "what is the
    return policy and refund process?". Meta-commentary about a document is not the
    document.
    """
    keep = [
        line
        for line in body.splitlines()
        if not line.strip().lower().startswith(_PROVENANCE_PREFIXES)
    ]
    return "\n".join(keep)


def _chunk_text(heading: str, body: str) -> str:
    if heading and body:
        return f"{heading}: {body}"
    return heading or body


def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split text on word boundaries when a single block exceeds the cap.

    Paragraph splitting is not enough: the shipping page is one 884-character list
    block, and an unbounded chunk is a keyword soup that outranks focused clauses.
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    current = ""
    for word in text.split():
        if current and len(current) + len(word) + 1 > max_chars:
            parts.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        parts.append(current)
    return parts or [text]


def _split_long(body: str, max_chars: int) -> list[str]:
    """Split a long section at paragraph boundaries, keeping each part under the cap.

    A heading-less list section (the shipping page) would otherwise become one huge
    keyword soup that, under a lexical embedder, outranks the focused clauses it is
    competing with. Every part keeps the heading, so identity survives the split.
    """
    if max_chars <= 0 or len(body) <= max_chars:
        return [_flatten(body)]
    parts: list[str] = []
    current = ""
    for block in body.split("\n\n"):
        block = _flatten(block)
        if not block:
            continue
        if current and len(current) + len(block) + 1 > max_chars:
            parts.append(current)
            current = block
        else:
            current = f"{current} {block}".strip()
    if current:
        parts.append(current)
    bounded: list[str] = []
    for part in parts or [body]:
        bounded.extend(_hard_split(part, max_chars))
    return bounded


def load_chunks(path: str, min_chars: int = 40, max_chars: int = 1000) -> list[Chunk]:
    root = Path(path)
    if not root.exists():
        return []

    chunks: list[Chunk] = []
    for file in sorted(root.glob("*.md")):
        text = file.read_text(encoding="utf-8")
        for index, (heading, body) in enumerate(_sections(text)):
            body = _strip_provenance(body)
            # Nothing left but a heading (or nothing at all) carries no rule, and
            # indexing it would put the document title in the corpus as content.
            if not _flatten(body):
                continue
            parts = _split_long(body, max_chars)
            for part_index, part in enumerate(parts):
                # The threshold applies to the whole chunk, heading included, so a
                # short clause is kept as long as it is named.
                chunk_text = _chunk_text(heading, part)
                if len(chunk_text) < min_chars:
                    continue
                suffix = f".{part_index}" if len(parts) > 1 else ""
                chunks.append(
                    Chunk(id=f"{file.name}#{index}{suffix}", text=chunk_text, source=file.name)
                )
    return chunks
