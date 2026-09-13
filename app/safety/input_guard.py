"""Deterministic input guard (feature 028, RW-1).

Classify a user message as ``ok``, ``injection``, or ``too_long`` **before** it
reaches the model. The guard normalizes first (NFKC folds fullwidth homoglyphs,
zero-width characters are stripped, whitespace is collapsed), then matches
instruction-override phrasing. It is pure, dependency-free, and cheap — it runs
before any spend (HR-12).

This is a lexical/structural layer, not a model classifier; a determined
adversary can evade it (documented as a residual gap). It exists to make the
common attacks have a defined, safe outcome.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff"

# Instruction-override / prompt-extraction phrasing. Each pattern requires enough
# context that a benign use of a single word does not trip it.
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"\bignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier|preceding)\s+"
        r"(instruction|prompt|rule|message|direction)s?\b",
        r"\bdisregard\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier|your)\s+"
        r"(instruction|prompt|rule|direction)s?\b",
        r"\b(reveal|show|print|repeat|output|leak|display)\s+(me\s+)?(your|the)\s+"
        r"(system\s+)?(prompt|instruction|rule)s?\b",
        r"\b(what|repeat)\s+(is|are|was|were)\s+your\s+(system\s+)?"
        r"(prompt|instruction|rule)s?\b",
        r"\byou\s+are\s+(now|no\s+longer)\b",
        r"\b(pretend|imagine)\s+(that\s+)?you\s+are\b",
        r"\b(developer|dev|debug|god)\s+mode\b",
        r"\b(jailbreak|do\s+anything\s+now|dan\s+mode)\b",
        r"\b(new|updated|revised)\s+(instruction|prompt|rule)s?\b",
        r"\boverride\s+(your|the)\s+(instruction|prompt|rule|safety)s?\b",
        r"\bfrom\s+now\s+on\s+you\s+(will|must|should)\b",
    )
)


@dataclass(frozen=True)
class GuardVerdict:
    """The guard's decision. ``message`` is the safe reply when blocked."""

    allowed: bool
    category: str = "ok"  # "ok" | "injection" | "too_long"
    message: str = ""

    @classmethod
    def allow(cls) -> GuardVerdict:
        return cls(True)

    @classmethod
    def block(cls, category: str, message: str) -> GuardVerdict:
        return cls(False, category, message)


REFUSAL_INJECTION = (
    "I can't help with that request. I can help you shop: search the catalog, check a "
    "product, manage your cart, or answer questions about orders, shipping, returns, "
    "and warranty."
)
REFUSAL_TOO_LONG = "That message is too long for me to process. Please shorten it and try again."


def normalize_input(text: str) -> str:
    """NFKC-fold, strip zero-width characters, and collapse whitespace."""
    folded = unicodedata.normalize("NFKC", text)
    stripped = "".join(ch for ch in folded if ch not in _ZERO_WIDTH)
    return " ".join(stripped.split())


def check_input(text: str, *, max_chars: int = 4000) -> GuardVerdict:
    """Classify a message. Blocks oversized input and injection attempts."""
    normalized = normalize_input(text)
    if len(normalized) > max_chars:
        return GuardVerdict.block("too_long", REFUSAL_TOO_LONG)
    lowered = normalized.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(lowered):
            return GuardVerdict.block("injection", REFUSAL_INJECTION)
    return GuardVerdict.allow()
