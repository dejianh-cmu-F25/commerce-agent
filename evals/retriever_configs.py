"""Retriever config names shared by the benchmarks (feature 046).

A name is a kind, optionally followed by RRF weights::

    tfidf | dense-hash | dense-openai | hybrid-openai | hybrid-bm25
    hybrid-openai-w3:1        # sparse weight 3, dense weight 1

Weighted names exist so a weighted fusion is a *first-class comparison* in the
same table as the unweighted one, instead of a separate ad-hoc script. The
weights themselves are chosen on a held-out split (``evals/tune_rrf.py``).
"""

from __future__ import annotations

import re

_WEIGHTED = re.compile(r"^(?P<kind>.+?)-w(?P<sparse>\d+(?:\.\d+)?):(?P<dense>\d+(?:\.\d+)?)$")


def parse_config(name: str) -> tuple[str, tuple[float, float] | None]:
    """``"hybrid-openai-w3:1"`` -> ``("hybrid-openai", (3.0, 1.0))``."""
    match = _WEIGHTED.match(name)
    if match is None:
        return name, None
    return match.group("kind"), (float(match.group("sparse")), float(match.group("dense")))


def config_name(kind: str, weights: tuple[float, float]) -> str:
    sparse, dense = weights
    return f"{kind}-w{sparse:g}:{dense:g}"
