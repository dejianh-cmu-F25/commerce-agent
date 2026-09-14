"""Simulated in-memory auth (feature 046). No real OAuth."""

from __future__ import annotations

from app.ports.auth import Principal


class InMemoryAuth:
    """Maps opaque tokens to principals; a demo stand-in for real OAuth."""

    def __init__(self, tokens: dict[str, Principal] | None = None) -> None:
        self._tokens = dict(tokens or {})

    def issue(self, token: str, principal: Principal) -> None:
        self._tokens[token] = principal

    def authenticate(self, token: str) -> Principal | None:
        return self._tokens.get(token)
