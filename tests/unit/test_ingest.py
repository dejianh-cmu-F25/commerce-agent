"""Knowledge ingestion keeps a clause with its heading (the clause's identity)."""

from __future__ import annotations

from pathlib import Path

from app.knowledge.ingest import load_chunks

DOC = """# Store policy

> Sourced from the policy file.

## returns#window-default

Most items can be returned within 30 days of delivery.

Rules: window_days=30

## returns#non-returnable

Perishables and final sale items cannot be returned.
"""


def _write(tmp_path: Path, text: str = DOC, name: str = "returns.md") -> str:
    (tmp_path / name).write_text(text)
    return str(tmp_path)


def test_a_heading_and_its_body_form_one_chunk(tmp_path: Path) -> None:
    chunks = load_chunks(_write(tmp_path))
    by_id = {chunk.id: chunk.text for chunk in chunks}
    clause = next(text for text in by_id.values() if "30 days" in text)
    assert clause.startswith("returns#window-default: "), clause
    # The rule lines stay with their clause rather than becoming their own chunk.
    assert "window_days=30" in clause


def test_a_short_but_named_clause_survives_the_threshold(tmp_path: Path) -> None:
    """Regression: the heading used to be dropped for being shorter than min_chars,
    so a rule arrived with nothing naming it and the model guessed the name."""
    short = "## returns#final-sale\n\nFinal sale items cannot be returned.\n"
    chunks = load_chunks(_write(tmp_path, short), min_chars=40)
    assert [chunk.text for chunk in chunks] == [
        "returns#final-sale: Final sale items cannot be returned."
    ]


def test_a_document_without_headings_still_chunks(tmp_path: Path) -> None:
    chunks = load_chunks(_write(tmp_path, "just a paragraph of policy text, long enough.\n"))
    assert len(chunks) == 1
    assert chunks[0].source == "returns.md"


def test_ids_are_stable_so_reingestion_is_idempotent(tmp_path: Path) -> None:
    path = _write(tmp_path)
    first = [chunk.id for chunk in load_chunks(path)]
    second = [chunk.id for chunk in load_chunks(path)]
    assert first == second
    assert len(set(first)) == len(first)


def test_a_missing_directory_yields_no_chunks(tmp_path: Path) -> None:
    assert load_chunks(str(tmp_path / "nope")) == []
