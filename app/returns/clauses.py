"""Load the machine-readable return policy clauses (feature 045).

The clauses are the harness's authoritative view of the policy: the model reads
prose, the harness verifies against these. Pure and dependency-free apart from
PyYAML, so the verifier is deterministic and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_POLICY_PATH = "config/policies/policies.yaml"


@dataclass(frozen=True)
class Clause:
    id: str
    version: str
    effective_from: str
    text: str
    window_days: int | None = None
    non_returnable_tags: tuple[str, ...] = ()
    restocking_fee_pct: float | None = None
    applies_to_tags: tuple[str, ...] = ()
    exception_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class Policy:
    active_version: str
    clauses: list[Clause] = field(default_factory=list)

    def by_id(self, clause_id: str) -> Clause | None:
        return next((clause for clause in self.clauses if clause.id == clause_id), None)


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> Policy:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    clauses = [
        Clause(
            id=str(entry["id"]),
            version=str(entry.get("version", "")),
            effective_from=str(entry.get("effective_from", "")),
            text=str(entry.get("text", "")),
            window_days=entry.get("window_days"),
            non_returnable_tags=tuple(entry.get("non_returnable_tags", ())),
            restocking_fee_pct=entry.get("restocking_fee_pct"),
            applies_to_tags=tuple(entry.get("applies_to_tags", ())),
            exception_reasons=tuple(entry.get("exception_reasons", ())),
        )
        for entry in raw.get("clauses", [])
    ]
    return Policy(active_version=str(raw.get("active_version", "")), clauses=clauses)
