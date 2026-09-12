"""Unit tests for the skills loader (feature 019)."""

from __future__ import annotations

from pathlib import Path

from app.skills.loader import Skill, SkillLibrary, load_skills


def _write(root: Path, name: str, text: str) -> None:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(text)


def test_loads_frontmatter_and_derives_missing(tmp_path: Path):
    _write(tmp_path, "alpha", "---\nname: alpha\ndescription: First skill\n---\nDo the thing.")
    _write(tmp_path, "beta", "Beta body line\n\nmore")

    library = load_skills(str(tmp_path))
    assert sorted(library.names()) == ["alpha", "beta"]

    alpha = library.get("alpha")
    assert alpha is not None
    assert alpha.description == "First skill"
    assert "Do the thing." in alpha.body

    beta = library.get("beta")
    assert beta is not None
    assert beta.name == "beta"
    assert beta.description == "Beta body line"

    assert "alpha: First skill" in library.catalog()


def test_missing_directory_is_empty(tmp_path: Path):
    library = load_skills(str(tmp_path / "nope"))
    assert len(library) == 0
    assert library.catalog() == ""


def test_duplicate_names_first_wins(tmp_path: Path):
    _write(tmp_path, "a", "---\nname: same\ndescription: first\n---\nbody")
    _write(tmp_path, "b", "---\nname: same\ndescription: second\n---\nbody")
    library = load_skills(str(tmp_path))
    assert len(library) == 1
    same = library.get("same")
    assert same is not None
    assert same.description == "first"


def test_library_from_list():
    library = SkillLibrary([Skill("x", "d", "b")])
    assert library.names() == ["x"]
    skill = library.get("x")
    assert skill is not None
    assert skill.body == "b"
