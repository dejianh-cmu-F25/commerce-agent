#!/usr/bin/env python3
"""Gate for Agent Notes (constitution DR-4).

Checks each note under ``docs/notes/`` for a valid path, a matching ``Status``,
a ``## Problem`` section, and a mandatory ``## Alternatives considered``
section. Implemented notes must use present-tense headings.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

NOTES_ROOT = Path("docs/notes")
LIFECYCLES = {"proposed", "implemented", "rejected"}
CLASSES = {"architecture", "process", "testing", "production"}
FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
IMPLEMENTED_REQUIRED = ("## Decision", "## Consequences")
IMPLEMENTED_FORBIDDEN = ("## Proposal", "## Plan", "## Acceptance criteria")


def fail(message: str) -> bool:
    print(f"FAIL: {message}")
    return False


def check_file(path: Path) -> bool:
    rel = path.relative_to(NOTES_ROOT)
    parts = rel.parts
    ok = True

    if len(parts) != 3:
        return fail(f"{rel}: expected <lifecycle>/<class>/<file>.md")

    lifecycle, cls, name = parts
    if lifecycle not in LIFECYCLES:
        ok = fail(f"{rel}: unknown lifecycle {lifecycle!r}")
    if cls not in CLASSES:
        ok = fail(f"{rel}: unknown class {cls!r}")
    if not FILENAME_RE.match(name):
        ok = fail(f"{rel}: filename must be yyyy-mm-dd-topic.md")

    text = path.read_text()
    if not text.startswith("# Agent Note: "):
        ok = fail(f"{rel}: first line must be '# Agent Note: <title>'")

    status_match = re.search(r"^Status: (.+)$", text, re.M)
    if not status_match:
        ok = fail(f"{rel}: missing 'Status:' line")
    elif not status_match.group(1).strip().startswith(lifecycle):
        ok = fail(f"{rel}: Status does not match folder {lifecycle!r}")

    if "## Problem" not in text:
        ok = fail(f"{rel}: missing '## Problem'")
    if "## Alternatives considered" not in text:
        ok = fail(f"{rel}: missing '## Alternatives considered'")

    if lifecycle == "implemented":
        for heading in IMPLEMENTED_REQUIRED:
            if heading not in text:
                ok = fail(f"{rel}: implemented note missing {heading!r}")
        for heading in IMPLEMENTED_FORBIDDEN:
            if heading in text:
                ok = fail(f"{rel}: implemented note must not contain {heading!r}")

    return ok


def main() -> int:
    if not NOTES_ROOT.exists():
        print("No docs/notes directory; nothing to check.")
        return 0

    files = sorted(NOTES_ROOT.rglob("*.md"))
    if not files:
        print("No agent notes yet; nothing to check.")
        return 0

    results = [check_file(path) for path in files]
    if all(results):
        print(f"OK: {len(files)} agent note(s) valid.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
