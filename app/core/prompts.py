"""Prompt loading.

Prompts live under ``config/prompts/`` and are never inlined in code (PB-4).
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path("config/prompts")


def load_prompt(name: str, prompts_dir: str | Path = PROMPTS_DIR) -> str:
    """Load a prompt file by name (without extension)."""
    path = Path(prompts_dir) / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text().strip()
