"""The passage index is wired into the live catalog behind a config switch (047).

Skipped when the gitignored catalog snapshot is absent, so the keyless gate does
not depend on the dataset.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.catalog_index import CatalogIndex, PassageCatalogIndex
from app.core.settings import load_settings

SNAPSHOT = Path("data/discovery/products.json")


@pytest.mark.skipif(not SNAPSHOT.exists(), reason="catalog snapshot not built")
def test_passages_off_is_the_document_index() -> None:
    from web.main import build_catalog_index

    settings = load_settings()
    settings.catalog.passages = False
    index = build_catalog_index(settings, enrich=True)
    assert isinstance(index, CatalogIndex)


@pytest.mark.skipif(not SNAPSHOT.exists(), reason="catalog snapshot not built")
def test_passages_on_is_the_passage_index() -> None:
    from web.main import build_catalog_index

    settings = load_settings()
    settings.catalog.passages = True
    index = build_catalog_index(settings, enrich=True)
    assert isinstance(index, PassageCatalogIndex)
    ids = index.search("something to keep my ears warm", 5)
    assert all(str(i).startswith("gid://") for i in ids)
