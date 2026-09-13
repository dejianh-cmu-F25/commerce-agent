"""Every change states its blast radius and rollback (feature 032, SC-4)."""

from __future__ import annotations

import json
from pathlib import Path

CHANGE_LOG = Path(__file__).resolve().parents[2] / "specs" / "change-log.json"


def test_every_entry_states_blast_radius_and_rollback() -> None:
    entries = json.loads(CHANGE_LOG.read_text())["entries"]
    assert entries, "the change log is empty"
    missing = [
        entry["change"]
        for entry in entries
        if not entry.get("blast_radius") or not entry.get("rollback")
    ]
    assert missing == [], f"entries missing blast radius/rollback: {missing}"
