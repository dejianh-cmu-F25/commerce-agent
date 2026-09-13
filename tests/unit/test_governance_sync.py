"""Governance consistency: DR-3 Agent Note classes match the gate (feature 026).

The class list lives in two places — the constitution (DR-3) and
``scripts/verify_notes.py`` — and must not drift.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / ".specify" / "memory" / "constitution.md"
VERIFY_NOTES = ROOT / "scripts" / "verify_notes.py"


def _constitution_classes() -> set[str]:
    match = re.search(r"classes (.+?)\.", CONSTITUTION.read_text(), re.S)
    assert match, "DR-3 classes not found in the constitution"
    return set(re.findall(r"`([a-z]+)`", match.group(1)))


def _verify_notes_classes() -> set[str]:
    match = re.search(r"CLASSES = \{([^}]+)\}", VERIFY_NOTES.read_text())
    assert match, "CLASSES not found in verify_notes.py"
    return {item.strip().strip('"').strip("'") for item in match.group(1).split(",")}


def test_agent_note_classes_match_the_gate():
    assert _constitution_classes() == _verify_notes_classes()
