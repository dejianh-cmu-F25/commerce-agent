"""Labeled retrieval set (feature 022).

Each case maps a query to the policy document that should ground the answer,
with a difficulty label (easy: keyword overlap; medium: paraphrase; hard:
multi-topic or negation). Adding a query is a data change (HR-11).

The corpus is the real, sourced policy set: ``amazon-returns.md`` (derived from
the policy SoT) and ``amazon-shipping.md`` (sourced from Amazon's shipping page).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_source: str  # the document file name, e.g. "amazon-returns.md"
    difficulty: str


RETRIEVAL_SET: list[RetrievalCase] = [
    # amazon-returns.md (derived from config/policies/amazon.yaml)
    RetrievalCase("how many days do I have to return an item?", "amazon-returns.md", "easy"),
    RetrievalCase("how long for a refund to arrive?", "amazon-returns.md", "medium"),
    RetrievalCase("who pays return shipping?", "amazon-returns.md", "medium"),
    RetrievalCase("can I return final sale items or gift cards?", "amazon-returns.md", "easy"),
    RetrievalCase("is return shipping free for a defective item?", "amazon-returns.md", "hard"),
    RetrievalCase("can I send something back after I opened it?", "amazon-returns.md", "hard"),
    RetrievalCase("what is the restocking fee?", "amazon-returns.md", "easy"),
    RetrievalCase("how long is the window for Apple products?", "amazon-returns.md", "medium"),
    RetrievalCase("are mattresses returnable?", "amazon-returns.md", "medium"),
    # amazon-shipping.md (sourced from Amazon's shipping help page)
    RetrievalCase("how do I track my package?", "amazon-shipping.md", "easy"),
    RetrievalCase("what if my package is late?", "amazon-shipping.md", "easy"),
    RetrievalCase("my package shows delivered but I can't find it", "amazon-shipping.md", "medium"),
    RetrievalCase("how are shipping rates determined?", "amazon-shipping.md", "medium"),
    RetrievalCase("what about international shipping?", "amazon-shipping.md", "medium"),
    RetrievalCase("is there special shipping for large items?", "amazon-shipping.md", "hard"),
    RetrievalCase("what is Prime shipping?", "amazon-shipping.md", "easy"),
    RetrievalCase("an item is missing from my package", "amazon-shipping.md", "hard"),
]


@dataclass(frozen=True)
class MultilingualCase:
    """A non-English query against the English corpus (feature 040, RW-1).

    Measured and reported as a gap; not gated, because the keyless lexical
    retriever cannot cross languages.
    """

    query: str
    expected_source: str
    language: str


MULTILINGUAL_SET: list[MultilingualCase] = [
    MultilingualCase("¿Cuántos días tengo para devolver un artículo?", "amazon-returns.md", "es"),
    MultilingualCase("¿Cuánto cuesta el envío estándar?", "amazon-shipping.md", "es"),
    MultilingualCase("¿Puedo devolver un artículo abierto?", "amazon-returns.md", "es"),
    MultilingualCase("Quel est le délai de livraison standard ?", "amazon-shipping.md", "fr"),
    MultilingualCase(
        "Combien de temps ai-je pour retourner un article ?", "amazon-returns.md", "fr"
    ),
    MultilingualCase("Wie lange habe ich Zeit für eine Rückgabe?", "amazon-returns.md", "de"),
    MultilingualCase("退货需要多少天？", "amazon-returns.md", "zh"),
    MultilingualCase("标准运费是多少？", "amazon-shipping.md", "zh"),
]
