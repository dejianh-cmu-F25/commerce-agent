"""Amazon return policy: the single source of truth + the deterministic engine (046).

The policy lives in ``config/policies/amazon.yaml`` (versioned, citable). This
module loads it and decides eligibility **deterministically** — no model decides
(HR-4). The harness validates the model's proposal against this engine at runtime.

Versioning is real: the active version is selected by ``active_version`` (or by
date via :func:`select_version`); a superseded version's clauses are never applied
to a decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

DEFAULT_AMAZON_POLICY_PATH = "config/policies/amazon.yaml"

ELIGIBLE = "eligible"
INELIGIBLE = "ineligible"
ESCALATE = "escalate"

# Categories that are returnable but carry a 100% restocking fee when opened/used.
_RESTOCKING_DEFAULT = ("opened_software", "video_games", "collectible_cards")


@dataclass(frozen=True)
class AmazonClause:
    id: str
    category: str
    paraphrase: str
    rules: dict
    source: str
    effective_from: str


@dataclass(frozen=True)
class AmazonPolicy:
    retailer: str
    active_version: str
    sources: dict[str, dict] = field(default_factory=dict)
    versions: dict[str, dict] = field(default_factory=dict)

    def version(self, name: str | None = None) -> dict:
        return self.versions.get(name or self.active_version, {})

    def clauses(self, name: str | None = None) -> list[AmazonClause]:
        version = self.version(name)
        source = str(version.get("source", ""))
        effective_from = str(version.get("effective_from", ""))
        return [
            AmazonClause(
                id=str(entry["id"]),
                category=str(entry.get("category", "all")),
                paraphrase=str(entry.get("paraphrase", "")),
                rules=dict(entry.get("rules", {})),
                source=source,
                effective_from=effective_from,
            )
            for entry in version.get("clauses", [])
        ]

    def clause(self, clause_id: str, name: str | None = None) -> AmazonClause | None:
        return next((c for c in self.clauses(name) if c.id == clause_id), None)

    def source_url(self, clause: AmazonClause) -> str:
        return str(self.sources.get(clause.source, {}).get("url", ""))


def select_version(policy: AmazonPolicy, at: datetime | None = None) -> str:
    """The version in force at ``at`` (latest ``effective_from`` <= at)."""
    at = at or datetime.now(UTC)
    best_name: str | None = None
    best_eff: datetime | None = None
    for name, spec in policy.versions.items():
        eff = _parse(str(spec.get("effective_from", "")))
        if eff is None or eff > at:
            continue
        if best_eff is None or eff > best_eff:
            best_name, best_eff = name, eff
    return best_name if best_name is not None else policy.active_version


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@dataclass(frozen=True)
class ReturnFacts:
    """The hard facts of one request (from the order + the item)."""

    order_id: str
    fulfillment_line_item_id: str
    reason: str  # unwanted | size_too_small | damaged | defective | wrong_item | missing
    delivered_at: str | None
    category: str = "all"  # e.g. electronics, apple_brand, digital_book, opened_software
    tags: tuple[str, ...] = ()
    on_order: bool = True


@dataclass(frozen=True)
class AmazonDecision:
    decision: str
    reasons: list[str] = field(default_factory=list)
    cited_clauses: list[str] = field(default_factory=list)
    fee_pct: float | None = None


def decide_return(
    facts: ReturnFacts,
    policy: AmazonPolicy,
    now: datetime | None = None,
    version: str | None = None,
) -> AmazonDecision:
    """Decide eligibility deterministically (the harness's "dispose" half)."""
    now = now or datetime.now(UTC)
    name = version or policy.active_version
    clauses = {c.id: c for c in policy.clauses(name)}

    if not facts.on_order:
        return AmazonDecision(
            ESCALATE, [f"item {facts.fulfillment_line_item_id} is not on order {facts.order_id}"]
        )

    non_ret = clauses.get("returns#non-returnable")
    non_returnable = set(non_ret.rules.get("non_returnable_categories", ())) if non_ret else set()
    exception = clauses.get("returns#exception")
    exception_reasons = set(exception.rules.get("exception_reasons", ())) if exception else set()
    is_exception = facts.reason in exception_reasons

    if facts.category in non_returnable or "final_sale" in facts.tags:
        if is_exception and exception is not None:
            return AmazonDecision(
                ESCALATE,
                [f"'{facts.reason}' on a non-returnable item is handled by Customer Service"],
                [non_ret.id, exception.id] if non_ret else [exception.id],
            )
        return AmazonDecision(
            INELIGIBLE,
            [f"category '{facts.category}' is non-returnable"],
            [non_ret.id] if non_ret else [],
        )

    if is_exception and exception is not None:
        # A defect is an exception, but not forever: past the exception window it is a
        # manufacturer warranty matter (returns#warranty is separate from a return).
        defect_window = exception.rules.get("exception_window_days") if exception else None
        delivered = _parse(facts.delivered_at)
        if defect_window is not None and delivered is not None:
            age = max(0, (now - delivered).days)
            if age > int(defect_window):
                warranty = clauses.get("returns#warranty")
                return AmazonDecision(
                    ESCALATE,
                    [
                        f"'{facts.reason}' after {age} days is a manufacturer warranty "
                        f"matter, not a return (the exception covers {defect_window} days)"
                    ],
                    [exception.id, warranty.id] if warranty else [exception.id],
                )
        return AmazonDecision(
            ELIGIBLE,
            [f"reason '{facts.reason}' is a policy exception (no window, no fee)"],
            [exception.id] if exception else [],
        )

    window = _window_days(facts.category, clauses)
    delivered = _parse(facts.delivered_at)
    if delivered is None:
        cited = [c.id for c in clauses.values() if "window_days" in c.rules]
        return AmazonDecision(
            ESCALATE, ["order has no delivery date; cannot compute the return window"], cited
        )

    age = max(0, (now - delivered).days)
    if age > window.days:
        return AmazonDecision(
            INELIGIBLE,
            [f"delivered {age} days ago; the window is {window.days} days"],
            [window.clause_id],
        )

    fee = _restocking_fee(facts.category, clauses)
    cited = [window.clause_id] + ([fee.clause_id] if fee else [])
    reasons = [f"within the {window.days}-day window"]
    if fee:
        reasons.append(f"a {fee.pct:g}% restocking fee applies")
    return AmazonDecision(ELIGIBLE, reasons, cited, fee.pct if fee else None)


@dataclass(frozen=True)
class _Window:
    days: int
    clause_id: str


@dataclass(frozen=True)
class _Fee:
    pct: float
    clause_id: str


def _window_days(category: str, clauses: dict[str, AmazonClause]) -> _Window:
    by_cat = clauses.get("returns#window-category")
    if by_cat and category in by_cat.rules.get("window_days_by_category", {}):
        return _Window(int(by_cat.rules["window_days_by_category"][category]), by_cat.id)
    default = clauses.get("returns#window-default")
    if default and "window_days" in default.rules:
        return _Window(int(default.rules["window_days"]), default.id)
    return _Window(0, "")


def _restocking_fee(category: str, clauses: dict[str, AmazonClause]) -> _Fee | None:
    fee = clauses.get("returns#fee-restocking")
    if not fee:
        return None
    categories = set(fee.rules.get("restocking_categories", _RESTOCKING_DEFAULT))
    if category in categories:
        return _Fee(float(fee.rules.get("restocking_fee_pct", 100)), fee.id)
    return None


def load_amazon_policy(path: str | Path = DEFAULT_AMAZON_POLICY_PATH) -> AmazonPolicy:
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return AmazonPolicy(
        retailer=str(raw.get("retailer", "amazon")),
        active_version=str(raw.get("active_version", "")),
        sources={str(s["id"]): dict(s) for s in raw.get("sources", [])},
        versions={str(k): dict(v) for k, v in raw.get("versions", {}).items()},
    )
