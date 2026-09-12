"""The ``use_skill`` tool (feature 019).

The model sees a skill catalog in the system prompt and loads a procedure's body
on demand. Bodies are external files (PB-4); loading is a normal tool call, so it
is traced and rendered like any step.
"""

from __future__ import annotations

from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.skills.loader import SkillLibrary
from app.tools.registry import ToolRegistry, ToolResult

USE_SKILL_SPEC = ToolSpec(
    name="use_skill",
    description=(
        "Load a skill's full procedure by name. Use a skill when its description "
        "matches the customer's request."
    ),
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "The skill name from the catalog."}
        },
        "required": ["name"],
    },
)


def register_skill_tools(registry: ToolRegistry, library: SkillLibrary) -> None:
    async def _use_skill(arguments: dict[str, Any], _session: Session) -> ToolResult:
        name = str(arguments.get("name", "")).strip()
        skill = library.get(name)
        if skill is None:
            available = ", ".join(library.names()) or "none"
            return ToolResult(
                content=f"Unknown skill: {name!r}. Available: {available}", status="error"
            )
        return ToolResult(content=f"Skill: {skill.name}\n\n{skill.body}")

    registry.register(USE_SKILL_SPEC, _use_skill)
