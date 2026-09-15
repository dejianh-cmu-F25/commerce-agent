"""Self-describing report metadata (feature 046, phase-1 hardening).

Reports drifted silently three times in one session: a guardrail row survived the
metric it described, the journey report kept quoting a failure that had been fixed,
and the audit predated a corpus it claimed to cover. Each time the numbers were
*wrong*, not obviously broken - which is the worst kind of wrong for evidence.

So every report under ``reports/`` (and ``evals/report.md``) now carries one
machine-readable line stating what produced it, how many cases it covers, and which
source files define that corpus along with their fingerprint. ``scripts/check_reports.py``
recomputes the fingerprint and compares the case count in the gate, so a report that
no longer matches its corpus **fails** instead of being trusted.

Hand-written reports declare the same line by hand: the point is that a report must
state its sources, whether or not a script emits it.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_MARKER = re.compile(r"<!--\s*report-meta:(?P<body>.*?)-->", re.DOTALL)
KNOWN_KEYS = ("generator", "cases", "sources", "fingerprint")


@dataclass(frozen=True)
class ReportMeta:
    generator: str
    cases: int
    sources: tuple[str, ...]
    fingerprint: str


def file_fingerprint(sources: Sequence[str | Path]) -> str:
    """A short, stable fingerprint of the files that define a corpus.

    Order-independent and content-addressed, so it changes when a case is added,
    edited or removed, and not when the files are merely listed differently.
    """
    digest = hashlib.sha1()
    for source in sorted(str(source) for source in sources):
        path = Path(source)
        if not path.is_absolute():
            path = ROOT / source
        content = path.read_bytes() if path.exists() else b"<missing>"
        digest.update(str(source).encode())
        digest.update(hashlib.sha1(content).digest())
    return digest.hexdigest()[:12]


def marker(generator: str, cases: int, sources: Sequence[str | Path] = ()) -> str:
    """The single metadata line a report must carry."""
    declared = ",".join(str(source) for source in sources)
    return (
        f"<!-- report-meta: generator={generator} cases={cases} "
        f"sources={declared} fingerprint={file_fingerprint(sources)} -->"
    )


def parse(text: str) -> ReportMeta | None:
    """Read the metadata line, or ``None`` when the report does not declare one."""
    match = _MARKER.search(text)
    if match is None:
        return None
    fields: dict[str, str] = {}
    for part in match.group("body").split():
        key, _, value = part.partition("=")
        fields[key.strip()] = value.strip()
    if not all(key in fields for key in KNOWN_KEYS):
        return None
    sources = tuple(s for s in fields["sources"].split(",") if s)
    try:
        cases = int(fields["cases"])
    except ValueError:
        return None
    return ReportMeta(fields["generator"], cases, sources, fields["fingerprint"])


def with_marker(text: str, generator: str, cases: int, sources: Sequence[str | Path]) -> str:
    """Prepend the metadata line, replacing one that is already there."""
    stripped = _MARKER.sub("", text).lstrip("\n")
    return f"{marker(generator, cases, sources)}\n\n{stripped}"
