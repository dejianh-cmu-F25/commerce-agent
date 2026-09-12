"""In-memory session repository (Service Provider for
:class:`app.ports.session_store.SessionRepository`).

Sessions live for the process lifetime; used for keyless runs and tests.
"""

from __future__ import annotations

from uuid import uuid4

from app.core.session import Session


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self) -> Session:
        session = Session(id=uuid4().hex)
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> Session:
        if session_id:
            existing = self._sessions.get(session_id)
            if existing is not None:
                return existing
        return self.create()

    def save(self, session: Session) -> None:
        self._sessions[session.id] = session
