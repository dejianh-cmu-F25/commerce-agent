"""Session persistence capability: Service Definition (constitution PB-2).

The session log is the source of truth (SL-1); persisting it lets a conversation
survive a restart and resume by id. Providers live in ``app/adapters`` and are
selected by configuration (PB-1).
"""

from __future__ import annotations

from typing import Protocol

from app.core.session import Session


class SessionRepository(Protocol):
    def create(self, customer_id: str = "") -> Session:
        """Create and persist a new session with a fresh id."""
        ...

    def get(self, session_id: str) -> Session | None:
        """Load a session, or ``None`` if it is unknown."""
        ...

    def get_or_create(self, session_id: str | None, customer_id: str = "") -> Session:
        """Load ``session_id`` if it exists, otherwise create a new session."""
        ...

    def save(self, session: Session) -> None:
        """Persist the session. Idempotent: re-saving adds no duplicates."""
        ...
