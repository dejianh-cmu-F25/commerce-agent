"""Local retrieval over the product catalog (feature 046, step A2).

Discovery used to call the shop's own keyword search: ~1.4 s per query and
hit@10 0.920 on our rule set, while the local retriever behind the same
``Retriever`` port scores 0.991 (tfidf) / 0.986 (hybrid) in 0.6-258 ms.

Two responsibilities, deliberately split:

- :class:`CatalogIndex` retrieves **ids** from a local index of the catalog's
  documents (``scripts/sync_catalog.py`` writes the snapshot).
- :class:`LocalSearchCatalog` turns those ids into live products by asking the
  catalog backend, so **price and stock are never read from the index**: the
  index decides what is relevant, the backend is the source of facts.

The document text is shared with the benchmark (:func:`catalog_document`) so the
offline baseline and the live path index exactly the same corpus.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

from app.core.types import Chunk, Order, Product
from app.ports.retriever import Retriever
from app.ports.storefront import StorefrontBackend
from app.reviews.clean import clean_review, is_usable_body

SNIPPET_CHARS = 200

_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")


class IdIndex(Protocol):
    """What `LocalSearchCatalog` needs: ids from a local index, facts from the shop."""

    def search(self, query: str, limit: int) -> list[str]: ...

    def record(self, product_id: str) -> dict[str, Any] | None: ...


def _review_snippets(product: dict[str, Any], reviews: Any, limit: int) -> list[str]:
    """Cleaned review text for a product, most helpful first.

    Reviews are keyed by the source ASIN, which the snapshot carries as ``sku``.
    """
    sku = str(product.get("sku") or "")
    if not sku:
        return []
    snippets: list[str] = []
    for review in reviews.get_reviews(sku, limit):
        text = clean_review(review.text, review.title)
        if is_usable_body(text):
            snippets.append(text[:SNIPPET_CHARS])
    return snippets


def catalog_document(
    product: dict[str, Any], *, reviews: Any | None = None, review_limit: int = 3
) -> str:
    """The searchable text of one product.

    Plain: title, vendor, type and public tags (``imported:*`` tags are provenance,
    not content). Enriched: the same plus the imported feature list and cleaned review
    evidence, which is the only place attribute claims ("runs small", "leaks") exist -
    no title states them.

    Kept in one place so the live index and ``evals/*_bench.py`` cannot drift apart.
    """
    tags = [tag for tag in product.get("tags") or [] if not tag.startswith("imported:")]
    parts = [
        product.get("title") or "",
        product.get("vendor") or "",
        product.get("type") or "",
        *tags,
    ]
    if reviews is not None:
        description = " ".join((product.get("description") or "").split())
        if description:
            parts.append(description)
        parts.extend(_review_snippets(product, reviews, review_limit))
    return " ".join(part for part in parts if part).strip()


def load_snapshot(path: str | Path) -> list[dict[str, Any]]:
    """Read the synced catalog snapshot; a missing file is an empty catalog."""
    file = Path(path)
    if not file.exists():
        return []
    try:
        products = json.loads(file.read_text())
    except json.JSONDecodeError:
        return []
    return products if isinstance(products, list) else []


def _feature_sentences(description: Any, *, min_chars: int = 25, limit: int = 6) -> list[str]:
    """Split a product's feature list into passage-sized pieces (feature 047).

    The feature text is a run of short claims ("GENTLE ON THE SKIN - ..."); one
    chunk per claim keeps each passage about one thing, which is what makes the
    evidence citable and the retrieval faithful.
    """
    text = " ".join(str(description or "").split())
    if not text:
        return []
    parts = [part.strip() for part in _SENTENCE.split(text) if part.strip()]
    kept = [part for part in parts if len(part) >= min_chars]
    return kept[:limit] or [text[:300]]


def catalog_chunks(
    product: dict[str, Any],
    *,
    reviews: Any | None = None,
    review_limit: int = 5,
    review_chars: int = 300,
) -> list[Chunk]:
    """Passage-level chunks for one product, each linked by ``product_id`` (047).

    Three passage kinds: a product summary (title/vendor/type/tags), one chunk per
    feature sentence, and one chunk per review. Every chunk carries the metadata a
    filter can use (``source``, ``product_id``, ``category``, ``price``, ``vendor``,
    and for reviews ``rating``/``verified``/``helpful_votes``).
    """
    pid = str(product["id"])
    base = {
        "product_id": pid,
        "category": str(product.get("type") or ""),
        "price": float(product.get("price") or 0.0),
        "vendor": str(product.get("vendor") or ""),
    }
    tags = [tag for tag in product.get("tags") or [] if not tag.startswith("imported:")]
    summary = " ".join(
        part
        for part in [
            product.get("title") or "",
            product.get("vendor") or "",
            product.get("type") or "",
            *tags,
        ]
        if part
    ).strip()
    chunks = [
        Chunk(
            id=f"{pid}#product",
            text=summary,
            source=pid,
            metadata={**base, "source": "product"},
        )
    ]
    for index, sentence in enumerate(_feature_sentences(product.get("description"))):
        chunks.append(
            Chunk(
                id=f"{pid}#desc{index}",
                text=sentence,
                source=pid,
                metadata={**base, "source": "description"},
            )
        )
    sku = str(product.get("sku") or "")
    if reviews is not None and sku:
        for index, review in enumerate(reviews.get_reviews(sku, review_limit)):
            text = clean_review(review.text, review.title)
            if not is_usable_body(text):
                continue
            chunks.append(
                Chunk(
                    id=f"{pid}#review{index}",
                    text=text[:review_chars],
                    source=pid,
                    metadata={
                        **base,
                        "source": "review",
                        "rating": float(review.rating),
                        "verified": bool(review.verified),
                        "helpful_votes": int(review.helpful_votes),
                    },
                )
            )
    return chunks


class PassageCatalogIndex:
    """Passage-level catalog index that aggregates chunk hits to products (047).

    Where :class:`CatalogIndex` indexes one document per product, this indexes each
    passage and links it back to its product: a query retrieves the most relevant
    passages (optionally filtered by metadata), then their scores are aggregated per
    product. The chunk hits are kept for chunk-level metrics and for citing the
    evidence an answer used.
    """

    def __init__(
        self,
        retriever: Retriever,
        products: list[dict[str, Any]],
        *,
        reviews: Any | None = None,
        chunks: list[Chunk] | None = None,
        review_limit: int = 5,
    ) -> None:
        self._retriever = retriever
        self._products = {str(p["id"]): p for p in products}
        materialised = (
            chunks
            if chunks is not None
            else [
                chunk
                for product in products
                for chunk in catalog_chunks(product, reviews=reviews, review_limit=review_limit)
            ]
        )
        self._chunk_count = len(materialised)
        self._retriever.add(materialised)

    def size(self) -> int:
        return len(self._products)

    def chunk_count(self) -> int:
        return self._chunk_count

    def retrieve_chunks(
        self, query: str, k: int, where: dict[str, Any] | None = None
    ) -> list[Chunk]:
        return [hit for hit in self._retriever.retrieve(query, k, where) if hit.id]

    def search(
        self,
        query: str,
        limit: int,
        *,
        where: dict[str, Any] | None = None,
        chunk_k: int = 100,
    ) -> list[str]:
        """Product ids ranked by their best passage, for a (filtered) query."""
        if limit <= 0 or not query.strip():
            return []
        best: dict[str, float] = {}
        for hit in self.retrieve_chunks(query, chunk_k, where):
            pid = str((hit.metadata or {}).get("product_id") or "")
            if pid not in self._products:
                continue
            best[pid] = max(best.get(pid, 0.0), hit.score)
        ranked = sorted(best, key=lambda pid: (-best[pid], pid))
        return ranked[:limit]

    def record(self, product_id: str) -> dict[str, Any] | None:
        return self._products.get(product_id)


class CatalogIndex:
    """A local index over the catalog snapshot. Returns ids, never facts."""

    def __init__(
        self,
        retriever: Retriever,
        products: list[dict[str, Any]],
        *,
        reviews: Any | None = None,
    ) -> None:
        self._retriever = retriever
        self._products = {str(p["id"]): p for p in products}
        self._retriever.add(
            [
                Chunk(
                    id=str(p["id"]),
                    text=catalog_document(p, reviews=reviews),
                    source=str(p["id"]),
                )
                for p in products
            ]
        )

    def size(self) -> int:
        return len(self._products)

    def search(self, query: str, limit: int) -> list[str]:
        if limit <= 0 or not query.strip():
            return []
        hits = self._retriever.retrieve(query, limit)
        return [hit.id for hit in hits if hit.id in self._products]

    def record(self, product_id: str) -> dict[str, Any] | None:
        return self._products.get(product_id)


class LocalSearchCatalog:
    """A catalog whose *search* is local retrieval and whose *facts* are live.

    ``overfetch`` widens the retrieval window before mapping to live products, so a
    product that has left the shop does not silently shrink the result set.

    Two indexes may be supplied: the plain one (title, vendor, type, tags) and an
    **enriched** one that also carries features and review evidence. The query class
    picks between them (``evidence``), because the two are a trade rather than an
    upgrade: measured, enrichment costs 0.037 hit@10 on lexical queries and buys 0.714
    on attribute queries, so each query should go to the index it fits.
    """

    def __init__(
        self,
        live: StorefrontBackend,
        index: IdIndex,
        *,
        enriched: IdIndex | None = None,
        overfetch: int = 4,
    ) -> None:
        self._live = live
        self._index = index
        self._enriched = enriched if enriched is not None else index
        self._overfetch = max(1, overfetch)

    def search(self, query: str, limit: int, *, evidence: bool = False) -> list[Product]:
        if limit <= 0:
            return []
        index = self._enriched if evidence else self._index
        ids = index.search(query, limit * self._overfetch)
        products: list[Product] = []
        for product_id in ids:
            product = self._live.get(product_id)
            if product is not None:
                products.append(product)
            if len(products) >= limit:
                break
        return products

    def get(self, product_id: str) -> Product | None:
        return self._live.get(product_id)

    def list_orders(self, customer_id: str) -> list[Order]:
        return self._live.list_orders(customer_id)

    def get_order(self, customer_id: str, order_id: str) -> Order | None:
        return self._live.get_order(customer_id, order_id)
