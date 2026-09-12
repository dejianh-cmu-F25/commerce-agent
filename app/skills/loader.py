"""Skills loader (feature 019, HR-11).

A skill is a directory ``skills/<name>/SKILL.md`` with an optional frontmatter
block (``name``, ``description``). Skills are external, static content (PB-4):
adding one is a new file, no code change. Loading is fail-soft — a missing
directory or malformed file never breaks startup.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_FRONTMATTER = "---"


@dataclass
class Skill:
    name: str
    description: str
    body: str


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for index in range(1, len(lines)):
        line = lines[index].strip()
        if line == _FRONTMATTER:
            return meta, "\n".join(lines[index + 1 :]).strip()
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    return {}, text.strip()  # no closing marker: the whole file is the body


def _load_one(path: Path) -> Skill | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    meta, body = _split_frontmatter(raw)
    name = (meta.get("name") or path.parent.name).strip()
    if not name:
        return None
    description = meta.get("description", "").strip()
    if not description:
        description = next((line.strip() for line in body.splitlines() if line.strip()), "")
    return Skill(name=name, description=description, body=body)


class SkillLibrary:
    def __init__(self, skills: list[Skill] | None = None) -> None:
        self._skills: dict[str, Skill] = {}
        for skill in skills or []:
            self._skills.setdefault(skill.name, skill)  # first wins on duplicates

    def __len__(self) -> int:
        return len(self._skills)

    def names(self) -> list[str]:
        return list(self._skills)

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def catalog(self) -> str:
        """A compact list of skills for the system prompt (HR-6)."""
        return "\n".join(f"- {skill.name}: {skill.description}" for skill in self._skills.values())


def load_skills(path: str) -> SkillLibrary:
    root = Path(path)
    if not root.is_dir():
        return SkillLibrary()
    skills: list[Skill] = []
    for skill_file in sorted(root.glob("*/SKILL.md")):
        skill = _load_one(skill_file)
        if skill is not None:
            skills.append(skill)
    return SkillLibrary(skills)
