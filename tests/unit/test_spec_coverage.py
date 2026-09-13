"""Every spec enumerates its real-world coverage (feature 035, RW-3)."""

from __future__ import annotations

import re
from pathlib import Path

SPECS = Path(__file__).resolve().parents[2] / "specs"
BULLETS = (
    "Input distribution",
    "Data quality",
    "Edge & failure modes",
    "Scale envelope",
    "Degradation",
    "Change evidence",
)


def _coverage(spec: Path) -> str:
    match = re.search(r"^## Real-World Coverage\s*$(.*?)(?=^## |\Z)", spec.read_text(), re.S | re.M)
    return match.group(1) if match else ""


def test_every_spec_has_the_six_coverage_bullets_with_content() -> None:
    specs = sorted(SPECS.glob("0*/spec.md"))
    assert specs, "no specs found"
    failures: list[str] = []
    for spec in specs:
        block = _coverage(spec)
        for bullet in BULLETS:
            found = re.search(rf"\*\*{re.escape(bullet)}\*\*:\s*(.+)", block)
            content = found.group(1).strip() if found else ""
            explained_na = re.match(r"n/?a\s*\(.+\)", content, re.I) is not None
            if found is None or (len(content) < 10 and not explained_na):
                failures.append(f"{spec.parent.name}: {bullet}")
    assert failures == [], f"specs missing coverage bullets: {failures}"
