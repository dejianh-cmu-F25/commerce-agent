"""RRF fusion weights: the lever that stops the weaker retriever dragging a fusion.

Measured need (reports/discovery-rrf-weights.md): equal weights cost 0.8 points of
hit@10 on the held-out half; down-weighting the dense leg recovers them.
"""

from __future__ import annotations

from app.adapters.retriever_hybrid import rrf_fuse
from app.core.types import Chunk


def _ranking(*ids: str) -> list[Chunk]:
    return [Chunk(id=i, text=i, source="s") for i in ids]


def test_equal_weights_tie_and_fall_back_to_the_id_order():
    fused = rrf_fuse([_ranking("a", "b"), _ranking("b", "a")], rrf_k=60, weights=(1.0, 1.0), k=2)
    assert [chunk.id for chunk in fused] == ["a", "b"]


def test_a_higher_sparse_weight_prefers_the_sparse_ranking():
    fused = rrf_fuse([_ranking("a", "b"), _ranking("b", "a")], rrf_k=60, weights=(3.0, 1.0), k=2)
    assert [chunk.id for chunk in fused] == ["a", "b"]


def test_a_higher_dense_weight_prefers_the_dense_ranking():
    fused = rrf_fuse([_ranking("a", "b"), _ranking("b", "a")], rrf_k=60, weights=(1.0, 3.0), k=2)
    assert [chunk.id for chunk in fused] == ["b", "a"]


def test_fusion_returns_the_union_with_scores():
    fused = rrf_fuse([_ranking("a", "b"), _ranking("c")], rrf_k=60, weights=(1.0, 1.0), k=5)
    assert {chunk.id for chunk in fused} == {"a", "b", "c"}
    assert all(chunk.score > 0 for chunk in fused)


def test_k_truncates_the_fused_ranking():
    fused = rrf_fuse(
        [_ranking("a", "b", "c"), _ranking("c", "b", "a")], rrf_k=60, weights=(1.0, 1.0), k=2
    )
    assert len(fused) == 2
