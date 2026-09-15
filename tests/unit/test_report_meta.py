"""Report metadata: a report states its corpus, and the fingerprint notices drift."""

from __future__ import annotations

from pathlib import Path

from app.evaluation.report_meta import file_fingerprint, marker, parse, with_marker


def _corpus(tmp_path: Path) -> str:
    path = tmp_path / "cases.jsonl"
    path.write_text('{"case_id": "a"}\n')
    return str(path)


def test_a_marker_round_trips():
    meta = parse(marker("evals/x.py", 3, []))
    assert meta is not None
    assert (meta.generator, meta.cases, meta.sources) == ("evals/x.py", 3, ())


def test_a_report_without_a_marker_is_rejected():
    assert parse("# just a report\n\nsome numbers\n") is None


def test_a_marker_missing_a_key_is_rejected():
    assert parse("<!-- report-meta: generator=x cases=1 -->") is None


def test_the_fingerprint_notices_a_changed_case(tmp_path: Path):
    corpus = _corpus(tmp_path)
    before = file_fingerprint([corpus])
    Path(corpus).write_text('{"case_id": "a"}\n{"case_id": "b"}\n')
    assert file_fingerprint([corpus]) != before


def test_the_fingerprint_ignores_the_order_of_the_sources(tmp_path: Path):
    first = _corpus(tmp_path)
    second = str(tmp_path / "other.jsonl")
    Path(second).write_text("{}\n")
    assert file_fingerprint([first, second]) == file_fingerprint([second, first])


def test_a_missing_source_is_still_fingerprinted(tmp_path: Path):
    """A report can declare a gitignored corpus; the check must still be stable."""
    missing = str(tmp_path / "nope.jsonl")
    assert file_fingerprint([missing]) == file_fingerprint([missing])


def test_with_marker_replaces_an_existing_marker(tmp_path: Path):
    corpus = _corpus(tmp_path)
    once = with_marker("# Report\n", "evals/x.py", 1, [corpus])
    twice = with_marker(once, "evals/x.py", 2, [corpus])
    assert twice.count("report-meta") == 1
    meta = parse(twice)
    assert meta is not None and meta.cases == 2
