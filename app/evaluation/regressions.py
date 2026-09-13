"""Regression registry: one durable guard per root-caused failure (033, RW-4/EV-5).

A regression names the failure, where it came from, its root cause, and a keyless
check. The check is referenced by name (a fixed map in the runner), so a promoted
entry cannot inject arbitrary code and a broken reference fails loud.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Regression:
    id: str
    source: str
    root_cause: str
    check: str


def load(path: str | Path) -> list[Regression]:
    data = json.loads(Path(path).read_text())
    return [
        Regression(
            id=entry["id"],
            source=entry["source"],
            root_cause=entry["root_cause"],
            check=entry["check"],
        )
        for entry in data.get("regressions", [])
    ]
