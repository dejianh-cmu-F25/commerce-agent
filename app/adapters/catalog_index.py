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
from pathlib import Path
from typing import Any

from app.core.types import Chunk, Order, Product
from app.ports.retriever import Retriever
from app.ports.storefront import StorefrontBackend


def catalog_document(product: dict[str, Any]) -> str:
    """The searchable text of one product: title, vendor, type and public tags.

    ``imported:*`` tags are provenance, not content. Kept in one place so the live
    index and ``evals/*_bench.py`` cannot drift apart.
    """
    tags = [tag for tag in product.get("tags") or [] if not tag.startswith("imported:")]
    return " ".join(
        [product.get("title") or "", product.get("vendor") or "", product.get("type") or "", *tags]
    ).strip()


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


class CatalogIndex:
    """A local index over the catalog snapshot. Returns ids, never facts."""

    def __init__(self, retriever: Retriever, products: list[dict[str, Any]]) -> None:
        self._retriever = retriever
        self._products = {str(p["id"]): p for p in products}
        self._retriever.add(
            [
                Chunk(id=str(p["id"]), text=catalog_document(p), source=str(p["id"]))
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
    """

    def __init__(self, live: StorefrontBackend, index: CatalogIndex, *, overfetch: int = 4) -> None:
        self._live = live
        self._index = index
        self._overfetch = max(1, overfetch)

    def search(self, query: str, limit: int) -> list[Product]:
        if limit <= 0:
            return []
        ids = self._index.search(query, limit * self._overfetch)
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
