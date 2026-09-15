"""Usage-based cost meter (Service Provider for :class:`app.ports.cost_meter.CostMeter`).

Accumulates token usage, converts to CNY, and persists the running total so a
budget survives restarts. Prices are USD per 1M tokens; the cap is CNY.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from app.core.settings import BudgetSettings
from app.core.types import Usage

# Persist at most every this many CNY. Writing the file on every model call is
# wasteful when many calls run concurrently; the worst case loss on a crash is
# one interval.
PERSIST_EVERY_CNY = 0.05


class UsageCostMeter:
    def __init__(self, settings: BudgetSettings) -> None:
        self._settings = settings
        self._state_path = Path(settings.state_file)
        self._spent_cny = self._load()
        self._persisted_cny = self._spent_cny
        self._headroom_cny = 0.0
        self._lock = threading.Lock()

    def set_headroom(self, cny: float) -> None:
        """Reserve budget for work already in flight.

        The loop checks the budget once per turn; with N turns running concurrently
        up to N turns can start before any of them is accounted for. Callers that
        run concurrently set this to N x (cost of one turn) so the cap still holds.
        """
        with self._lock:
            self._headroom_cny = max(0.0, cny)

    def flush(self) -> None:
        """Persist the running total now (call after a batch of work)."""
        with self._lock:
            self._persist()

    def _load(self) -> float:
        if not self._state_path.exists():
            return 0.0
        try:
            data = json.loads(self._state_path.read_text())
            return float(data.get("spent_cny", 0.0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0.0

    def _persist(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps({"spent_cny": round(self._spent_cny, 6)}))
        self._persisted_cny = self._spent_cny

    def cost_of(self, usage: Usage) -> float:
        """Cost of one call, in CNY.

        When the provider reports a cache breakdown, use it. Otherwise treat all
        prompt tokens as cache misses.
        """
        s = self._settings
        if usage.cache_hit_tokens or usage.cache_miss_tokens:
            cache_miss = usage.cache_miss_tokens
            cache_hit = usage.cache_hit_tokens
        else:
            cache_miss = usage.prompt_tokens
            cache_hit = 0
        usd = (
            cache_miss / 1_000_000 * s.input_cache_miss_per_1m
            + cache_hit / 1_000_000 * s.input_cache_hit_per_1m
            + usage.completion_tokens / 1_000_000 * s.output_per_1m
        )
        return usd * s.usd_to_cny

    def record(self, usage: Usage) -> None:
        with self._lock:
            self._spent_cny += self.cost_of(usage)
            if self._spent_cny - self._persisted_cny >= PERSIST_EVERY_CNY:
                self._persist()

    def spent_cny(self) -> float:
        return self._spent_cny

    def limit_cny(self) -> float:
        return self._settings.total_limit

    def remaining_cny(self) -> float:
        return max(0.0, self._settings.total_limit - self._spent_cny)

    def over_budget(self) -> bool:
        if not self._settings.enabled:
            return False
        return self._spent_cny + self._headroom_cny >= self._settings.total_limit


class NullCostMeter:
    """A no-op meter for tests and keyless runs."""

    def spent_cny(self) -> float:
        return 0.0

    def limit_cny(self) -> float:
        return 0.0

    def remaining_cny(self) -> float:
        return 0.0

    def over_budget(self) -> bool:
        return False

    def record(self, usage: Usage) -> None:
        return None

    def set_headroom(self, cny: float) -> None:
        return None

    def flush(self) -> None:
        return None
