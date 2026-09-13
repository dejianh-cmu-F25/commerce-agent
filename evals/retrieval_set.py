"""Labeled retrieval set (feature 022).

Each case maps a query to the policy document that should ground the answer,
with a difficulty label (easy: keyword overlap; medium: paraphrase; hard:
multi-topic or negation). Adding a query is a data change (HR-11).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_source: str  # the document file name, e.g. "returns.md"
    difficulty: str


RETRIEVAL_SET: list[RetrievalCase] = [
    # returns.md
    RetrievalCase("how many days do I have to return an item?", "returns.md", "easy"),
    RetrievalCase("can I get a full refund?", "returns.md", "easy"),
    RetrievalCase("do items need to be unused to return?", "returns.md", "medium"),
    RetrievalCase("how long for a refund to arrive?", "returns.md", "medium"),
    RetrievalCase("who pays return shipping?", "returns.md", "medium"),
    RetrievalCase("can I return final sale items or gift cards?", "returns.md", "easy"),
    RetrievalCase("how do I start a return?", "returns.md", "easy"),
    RetrievalCase("is return shipping free for a defective item?", "returns.md", "hard"),
    RetrievalCase("can I send something back after I opened it?", "returns.md", "hard"),
    # shipping.md
    RetrievalCase("how much does standard shipping cost?", "shipping.md", "easy"),
    RetrievalCase("how fast is expedited shipping?", "shipping.md", "easy"),
    RetrievalCase("do orders over 75 ship free?", "shipping.md", "medium"),
    RetrievalCase("do you ship to PO boxes?", "shipping.md", "medium"),
    RetrievalCase("how do I get tracking?", "shipping.md", "easy"),
    RetrievalCase("when do expedited orders ship?", "shipping.md", "medium"),
    RetrievalCase("how many business days does standard shipping take?", "shipping.md", "easy"),
    RetrievalCase("does free shipping apply outside the continental US?", "shipping.md", "hard"),
    RetrievalCase("will my order arrive before the weekend?", "shipping.md", "hard"),
    # warranty.md
    RetrievalCase("how long is the manufacturer warranty?", "warranty.md", "easy"),
    RetrievalCase("does the warranty cover broken zippers?", "warranty.md", "easy"),
    RetrievalCase("is normal wear and tear covered?", "warranty.md", "medium"),
    RetrievalCase("does the warranty cover accidental damage?", "warranty.md", "medium"),
    RetrievalCase("how do I make a warranty claim?", "warranty.md", "easy"),
    RetrievalCase("are failed seams covered?", "warranty.md", "medium"),
    RetrievalCase("what does the warranty cover?", "warranty.md", "easy"),
    RetrievalCase("are approved claims repaired or replaced?", "warranty.md", "medium"),
    RetrievalCase("my jacket seam came apart, is that covered?", "warranty.md", "hard"),
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
    MultilingualCase("¿Cuántos días tengo para devolver un artículo?", "returns.md", "es"),
    MultilingualCase("¿Cuánto cuesta el envío estándar?", "shipping.md", "es"),
    MultilingualCase("Combien de temps ai-je pour retourner un article ?", "returns.md", "fr"),
    MultilingualCase("Quel est le délai de livraison standard ?", "shipping.md", "fr"),
    MultilingualCase("Wie lange ist die Herstellergarantie?", "warranty.md", "de"),
    MultilingualCase("Wie viel kostet der Standardversand?", "shipping.md", "de"),
    MultilingualCase("退货需要多少天？", "returns.md", "zh"),
    MultilingualCase("标准运费是多少？", "shipping.md", "zh"),
]
