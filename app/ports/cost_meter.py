"""Cost meter capability: Service Definition (constitution HR-12).

The harness enforces a spend budget. The loop asks the meter before each model
call and records usage after it.
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Usage


class CostMeter(Protocol):
    def spent_cny(self) -> float: ...

    def limit_cny(self) -> float: ...

    def remaining_cny(self) -> float: ...

    def over_budget(self) -> bool: ...

    def record(self, usage: Usage) -> None:
        """Add the cost of one model call to the running total."""
        ...
