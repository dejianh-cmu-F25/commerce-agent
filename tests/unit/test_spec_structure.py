"""Every active spec carries the required sections (feature 045).

Best-practice structure for agent/LLM product specs: the core sections are always
required; the rest are required when the feature triggers them. Archived specs
(``specs/archive/``) are out of scope.
"""

from __future__ import annotations

from pathlib import Path

SPECS = Path(__file__).resolve().parents[2] / "specs"
CORE = ("## Requirements", "## Success Criteria", "## Assumptions", "## Real-World Coverage")
RW_MARKERS = (
    "tool",
    "retriev",
    "model",
    "prompt",
    "knowledge",
    "memory",
    "llm",
    "order",
    "policy",
    "input",
    "data",
)
HITL_MARKERS = ("propose", "approve", "refund", "human-in-the-loop", "human approval")
PROVENANCE_MARKERS = ("license", "shopify", "esci", "public policy", "external data")


def _specs() -> list[Path]:
    return sorted(p for p in SPECS.glob("0*/spec.md"))


def _missing(text: str) -> list[str]:
    missing = [section for section in CORE if section not in text]
    lowered = text.lower()
    if "## Web Acceptance" in text:
        if "## Observability" not in text:
            missing.append("## Observability (web-visible)")
        if "## UI Requirements" not in text:
            missing.append("## UI Requirements (web-visible)")
    if any(marker in lowered for marker in RW_MARKERS) and "## Evaluation Plan" not in text:
        missing.append("## Evaluation Plan (model/data feature)")
    if any(marker in lowered for marker in HITL_MARKERS) and "## Human-in-the-Loop" not in text:
        missing.append("## Human-in-the-Loop (proposes a state change)")
    if any(marker in lowered for marker in PROVENANCE_MARKERS) and "## Data Provenance" not in text:
        missing.append("## Data Provenance (external data)")
    return missing


def test_active_specs_have_required_sections() -> None:
    specs = _specs()
    assert specs, "no active specs found"
    failures = {spec.parent.name: _missing(spec.read_text()) for spec in specs}
    failures = {name: gaps for name, gaps in failures.items() if gaps}
    assert not failures, f"specs missing sections: {failures}"


def test_archived_specs_are_not_scanned() -> None:
    archived = list((SPECS / "archive").glob("0*/spec.md"))
    assert archived, "expected archived specs to exist"
    # The active glob must not pick up archived specs.
    assert not any("archive" in str(spec) for spec in _specs())
