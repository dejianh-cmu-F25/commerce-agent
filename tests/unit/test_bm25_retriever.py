"""BM25: saturation and length normalisation, and the Retriever contract."""

from __future__ import annotations

from app.adapters.retriever_bm25 import Bm25Retriever
from app.adapters.retriever_memory import InMemoryRetriever
from app.core.types import Chunk


def _chunk(cid: str, text: str) -> Chunk:
    return Chunk(id=cid, text=text, source="s")


def test_it_scores_a_rare_term_above_a_common_one():
    retriever = Bm25Retriever()
    retriever.add(
        [
            _chunk("a", "tent tent tent camping"),
            _chunk("b", "tent sleeping bag"),
            _chunk("c", "tent pillow"),
            _chunk("d", "tent lamp"),
        ]
    )
    # "camping" appears once, so it must dominate; "tent" is in every document and
    # carries no discriminating power.
    assert [chunk.id for chunk in retriever.retrieve("tent camping", 1)] == ["a"]


def test_term_frequency_saturates_instead_of_scaling_linearly():
    retriever = Bm25Retriever()
    retriever.add([_chunk("once", "lantern"), _chunk("many", "lantern " * 20)])
    once = retriever.retrieve("lantern", 2)
    scores = {chunk.id: chunk.score for chunk in once}
    # Ten times the term frequency must not mean ten times the score.
    assert scores["many"] > scores["once"]
    assert scores["many"] < scores["once"] * 10


def test_length_normalisation_prefers_the_shorter_document():
    retriever = Bm25Retriever()
    retriever.add([_chunk("short", "water bottle"), _chunk("long", "water bottle " + "x " * 100)])
    assert [chunk.id for chunk in retriever.retrieve("water bottle", 1)] == ["short"]


def test_the_contract_matches_the_other_retrievers():
    retriever = Bm25Retriever()
    retriever.add([_chunk("a", "camping stove"), _chunk("b", "camping stove")])
    assert retriever.size() == 2
    retriever.add([_chunk("a", "camping stove")])  # idempotent (RD-2)
    assert retriever.size() == 2
    assert retriever.retrieve("", 3) == []
    assert retriever.retrieve("nothing-matches-this", 3) == []
    assert len(retriever.retrieve("camping", 1)) == 1


def test_its_scores_are_a_different_function_from_tfidf():
    """Same order here, different maths.

    TF-IDF rewards raw term frequency and ignores length; BM25 saturates the term
    frequency and normalises by length. On a skewed document the scores therefore
    diverge even when both retrievers happen to agree on the winner - which is the
    honest reading for a corpus of short, near-uniform documents, and the reason the
    benchmark, not intuition, decides whether the swap helps.
    """
    chunks = [
        _chunk("a", "backpack hiking"),
        _chunk("b", "backpack " + "trail " * 30),
    ]
    tfidf = InMemoryRetriever()
    bm25 = Bm25Retriever()
    tfidf.add(chunks)
    bm25.add(chunks)

    tfidf_scores = {chunk.id: chunk.score for chunk in tfidf.retrieve("backpack trail", 2)}
    bm25_scores = {chunk.id: chunk.score for chunk in bm25.retrieve("backpack trail", 2)}

    assert set(tfidf_scores) == set(bm25_scores)
    assert tfidf_scores != bm25_scores
