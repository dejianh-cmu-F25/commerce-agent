"""Metadata filters, the passage index, and the chunk->product link (feature 047)."""

from __future__ import annotations

from app.adapters.catalog_index import PassageCatalogIndex, catalog_chunks
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.vector_memory import InMemoryVectorStore
from app.core.filters import metadata_matches, to_chroma_where
from app.core.types import Chunk


def test_metadata_matches_equality_range_and_membership() -> None:
    meta = {"source": "review", "rating": 5, "price": 10.0}
    assert metadata_matches(meta, None)
    assert metadata_matches(meta, {})
    assert metadata_matches(meta, {"source": "review"})
    assert not metadata_matches(meta, {"source": "description"})
    assert metadata_matches(meta, {"rating": {"$gte": 4}})
    assert not metadata_matches(meta, {"rating": {"$gte": 6}})
    assert metadata_matches(meta, {"source": {"$in": ["review", "description"]}})
    assert not metadata_matches(meta, {"source": {"$in": ["description"]}})
    assert metadata_matches(meta, {"rating": {"$ne": 4}})
    # a missing field never satisfies a condition
    assert not metadata_matches(meta, {"verified": True})
    assert not metadata_matches(meta, {"rating": {"$gt": 5}})


def test_to_chroma_where_wraps_multiple_conditions() -> None:
    assert to_chroma_where(None) is None
    assert to_chroma_where({"source": "review"}) == {"source": {"$eq": "review"}}
    assert to_chroma_where({"source": "review", "rating": {"$gte": 4}}) == {
        "$and": [{"source": {"$eq": "review"}}, {"rating": {"$gte": 4}}]
    }


def test_in_memory_vector_store_filters_candidates() -> None:
    store = InMemoryVectorStore()
    store.upsert(
        [
            Chunk(id="a", text="x", source="p", metadata={"source": "review"}),
            Chunk(id="b", text="y", source="p", metadata={"source": "description"}),
        ],
        [[1.0, 0.0], [1.0, 0.0]],
    )
    assert [c.id for c in store.query([1.0, 0.0], 5)] == ["a", "b"]
    assert [c.id for c in store.query([1.0, 0.0], 5, where={"source": "review"})] == ["a"]
    # metadata is preserved on the way out
    assert store.query([1.0, 0.0], 1)[0].metadata["source"] == "review"


class _StubReviews:
    """A minimal review store keyed by sku, enough to build passages."""

    def __init__(self, by_sku: dict[str, list]) -> None:
        self._by_sku = by_sku

    def get_reviews(self, product_id: str, limit: int = 5) -> list:
        return self._by_sku.get(product_id, [])[:limit]


class _Review:
    def __init__(self, text: str, rating: float, verified: bool = True) -> None:
        self.title = ""
        self.text = text
        self.rating = rating
        self.verified = verified
        self.helpful_votes = 3


def _product(pid: str, description: str) -> dict:
    return {
        "id": pid,
        "sku": f"SKU-{pid}",
        "title": "Acme Product",
        "vendor": "Acme",
        "type": "Outdoor",
        "tags": ["imported:reviews23"],
        "price": 42.0,
        "description": description,
    }


def test_catalog_chunks_are_linked_and_carry_metadata() -> None:
    product = _product("p1", "Lightweight and packs down small for the trail.")
    reviews = _StubReviews(
        {"SKU-p1": [_Review("Kept me completely dry on rainy days outside on the trail.", 5.0)]}
    )
    chunks = catalog_chunks(product, reviews=reviews)

    kinds = {chunk.metadata["source"] for chunk in chunks}
    assert kinds == {"product", "description", "review"}
    assert all(chunk.metadata["product_id"] == "p1" for chunk in chunks)
    review = next(chunk for chunk in chunks if chunk.metadata["source"] == "review")
    assert review.metadata["rating"] == 5.0
    assert review.metadata["verified"] is True
    assert review.source == "p1"  # the link back to the product


def _index() -> PassageCatalogIndex:
    products = [
        _product("p1", "Lightweight and packs down small for the trail."),
        _product("p2", "A sturdy option built for long trips outdoors."),
    ]
    reviews = _StubReviews(
        {
            "SKU-p1": [_Review("Kept me completely dry on rainy days outside on the trail.", 5.0)],
            "SKU-p2": [
                _Review(
                    "Fine, but nothing particularly special about it in my opinion.",
                    3.0,
                    verified=False,
                )
            ],
        }
    )
    return PassageCatalogIndex(InMemoryRetriever(), products, reviews=reviews)


def test_passage_index_aggregates_chunks_to_products() -> None:
    index = _index()
    # "rainy days" appears only in p1's review
    assert index.search("rainy days", 10) == ["p1"]


def test_passage_index_filters_by_metadata() -> None:
    index = _index()
    # filter to reviews only: p1 (its review matches) survives, p2 (no matching review) does not
    assert index.search("rainy days", 10, where={"source": "review"}) == ["p1"]
    assert index.search("rainy days", 10, where={"source": "description"}) == []
    # a rating floor keeps only high-rated reviews
    assert index.search("outside", 10, where={"rating": {"$gte": 4}}) == ["p1"]
    assert index.search("fine", 10, where={"rating": {"$gte": 4}}) == []
