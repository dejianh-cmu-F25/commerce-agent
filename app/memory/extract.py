"""Deterministic, keyless memory extraction (feature 013).

Facts are derived only from the customer's own text (P4) and only from a bounded
set of durable patterns. There is no model call, no network, and no
nondeterminism (P8): the same input always yields the same facts. Questions and
statements with no durable content produce nothing.

An LLM-assisted extractor is deferred; if added it must fall back to this
deterministic extractor (RD-1).
"""

from __future__ import annotations

import re

KIND_PREFERENCE = "preference"
KIND_CONSTRAINT = "constraint"
KIND_PROFILE = "profile"

_MAX_VALUE = 60

_SIZE_WORDS = {
    "xs": "XS",
    "s": "S",
    "m": "M",
    "l": "L",
    "xl": "XL",
    "xxl": "XXL",
    "small": "S",
    "medium": "M",
    "large": "L",
}

# A value capture stops before a new clause introduced by a pronoun.
_STOP = r"(?=\s+(?:and|but|so)\s+(?:i|we)\b|$)"

_SIZE_RE = re.compile(
    r"\b(?:my\s+size\s+is|i(?:'m| am)\s+a|i\s+(?:usually\s+)?wear(?:\s+a)?|size)\s+"
    r"(?:size\s+)?(xs|s|m|l|xl|xxl|small|medium|large|\d{1,2}(?:\.\d)?)\b",
    re.I,
)
_AVOID_RE = re.compile(
    r"\b(?:i(?:'m| am)\s+)?(?:allergic\s+to|avoid|can'?t\s+(?:wear|use|eat)|"
    r"don'?t\s+(?:like|wear|use|eat))\s+(.+?)" + _STOP,
    re.I,
)
_PREFER_RE = re.compile(r"\bi\s+(?:really\s+)?(?:like|love|prefer|enjoy)\s+(.+?)" + _STOP, re.I)
_OWN_RE = re.compile(
    r"\bi\s+(?:already\s+own|own|already\s+have)\s+(.+?)" + _STOP,
    re.I,
)
_BUDGET_RE = re.compile(
    r"\b(?:my\s+budget\s+is|budget\s+of|i\s+can\s+spend|i\s+want\s+to\s+spend|"
    r"i(?:'m| am)\s+willing\s+to\s+spend)\s+\$?(\d[\d,]*)",
    re.I,
)

_STOP_VALUES = {"it", "that", "this", "them", "those", "you", "me"}


def _clauses(text: str) -> list[str]:
    """Split into sentence-like clauses; questions are excluded later."""
    return [clause for clause in re.split(r"(?<=[.!?])\s+|\n+", text) if clause.strip()]


def _value(raw: str) -> str | None:
    value = re.split(r"[.!?\n]", raw.strip(), maxsplit=1)[0]
    value = re.sub(r"\s+", " ", value).strip(" .,;:!?\"'")
    value = re.sub(r"\s+(?:and|or|but)$", "", value, flags=re.I)
    if len(value) > _MAX_VALUE:
        value = value[:_MAX_VALUE].rsplit(" ", 1)[0].strip()
    if len(value) < 2 or value.lower() in _STOP_VALUES:
        return None
    return value


def extract_facts(text: str) -> list[tuple[str, str]]:
    """Return deterministic ``(kind, fact_text)`` pairs from the customer's text."""
    facts: dict[tuple[str, str], None] = {}

    for clause in _clauses(text):
        if clause.strip().endswith("?"):
            continue  # a question is not a durable statement about the customer

        for match in _SIZE_RE.finditer(clause):
            token = match.group(1).lower()
            size = _SIZE_WORDS.get(token, token)
            facts[(KIND_PROFILE, f"Wears size {size}")] = None

        for match in _AVOID_RE.finditer(clause):
            value = _value(match.group(1))
            if value:
                facts[(KIND_CONSTRAINT, f"Avoids {value}")] = None

        for match in _PREFER_RE.finditer(clause):
            value = _value(match.group(1))
            if value:
                facts[(KIND_PREFERENCE, f"Prefers {value}")] = None

        for match in _OWN_RE.finditer(clause):
            value = _value(match.group(1))
            if value:
                facts[(KIND_PROFILE, f"Owns {value}")] = None

        for match in _BUDGET_RE.finditer(clause):
            amount = match.group(1).replace(",", "")
            facts[(KIND_CONSTRAINT, f"Budget ${amount}")] = None

    return list(facts)
