"""Deterministic query-noise generator (feature 046, real-user realism).

Real users type in lowercase, drop punctuation, misspell, and speak in disfluent
fragments. These perturbations are deterministic (seeded) so the noisy corpus is
reproducible, and they are used to measure the **invariance** of behaviour under
noise (CheckList INV): the intent is unchanged, so the expected tools must not change.
"""

from __future__ import annotations

import random
import re

_PUNCT = re.compile(r"[?.!,;:\"']")
_DISFLUENCY = ("um, ", "uh, ", "so, ", "hi, ", "hey, ")


def lowercase(text: str) -> str:
    return text.lower()


def strip_punctuation(text: str) -> str:
    return _PUNCT.sub("", text)


def swap_adjacent(text: str, rng: random.Random) -> str:
    words = text.split()
    for index in range(len(words) - 1):
        if rng.random() < 0.4:
            a, b = words[index][:1], words[index][1:]
            if b:
                words[index] = b[:1] + a + b[1:]
    return " ".join(words)


def drop_letter(text: str, rng: random.Random) -> str:
    words: list[str] = []
    for word in text.split():
        if len(word) > 4 and rng.random() < 0.5:
            index = rng.randrange(1, len(word) - 1)
            word = word[:index] + word[index + 1 :]
        words.append(word)
    return " ".join(words)


def add_disfluency(text: str, rng: random.Random) -> str:
    return rng.choice(_DISFLUENCY) + text[:1].lower() + text[1:]


def variants(text: str, seed: int = 0) -> list[tuple[str, str]]:
    """Return ``(kind, noisy_text)`` pairs (one per perturbation kind)."""
    rng = random.Random(f"{seed}:{text}")
    return [
        ("lowercase", lowercase(text)),
        ("no_punctuation", strip_punctuation(text)),
        ("typo", drop_letter(text, rng)),
        ("swap", swap_adjacent(text, rng)),
        ("disfluency", add_disfluency(text, rng)),
    ]


def real_variants(text: str, seed: int = 0) -> list[tuple[str, str]]:
    """Variants that actually change the text.

    ``lowercase`` is a no-op for already-lowercase input, and a no-op variant is a
    duplicate case that double-counts and measures nothing (see the eval audit).
    """
    return [(kind, noisy) for kind, noisy in variants(text, seed) if noisy != text]


def _sanity() -> None:  # pragma: no cover - manual probe
    for kind, text in variants("I want to return an item, please."):
        print(kind, "->", text)


if __name__ == "__main__":  # pragma: no cover
    _sanity()
