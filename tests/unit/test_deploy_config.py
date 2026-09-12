"""Config-contract parity tests (feature 015, PB-1, DP-2)."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.settings import _ENV_OVERRIDES

ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = ROOT / ".env.example"
COMPOSE = ROOT / "docker-compose.yml"
DOCKERIGNORE = ROOT / ".dockerignore"

_KNOWN = set(_ENV_OVERRIDES)


def _env_example_keys() -> set[str]:
    keys: set[str] = set()
    for line in ENV_EXAMPLE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip())
    return keys


def _compose_env_keys() -> set[str]:
    data = yaml.safe_load(COMPOSE.read_text())
    environment = data["services"]["app"].get("environment") or {}
    return set(environment)


def test_env_example_documents_exactly_the_known_overrides():
    assert _env_example_keys() == _KNOWN


def test_compose_uses_only_known_env_keys():
    keys = _compose_env_keys()
    assert keys, "compose should set the app's config explicitly"
    assert keys <= _KNOWN


def test_dockerignore_keeps_secrets_and_runtime_data_out_of_the_image():
    ignored = {
        line.strip()
        for line in DOCKERIGNORE.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert ".env" in ignored
    assert "data" in ignored
    assert "logs" in ignored
