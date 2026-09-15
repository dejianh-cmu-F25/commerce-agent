"""The ``search_knowledge`` tool, backed by an injected retriever.

Answers about store policy come from retrieved chunks with their source document
(P4). No component: the result renders as a tool step.
"""

from __future__ import annotations

from typing import Any

from app.core.session import Session
from app.core.types import ToolSpec
from app.ports.retriever import Retriever
from app.tools.registry import ToolRegistry, ToolResult

SEARCH_KNOWLEDGE_SPEC = ToolSpec(
    name="search_knowledge",
    description=(
        "Search the store's published policy documents (shipping, returns) when the "
        "CUSTOMER asks a policy question. Always cite the source document. Do not use "
        "this to resolve an internal decision such as a return eligibility call - the "
        "harness supplies the clauses for those."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The policy question."},
            "k": {"type": "integer", "description": "Max snippets (default 3).", "minimum": 1},
        },
        "required": ["query"],
    },
)


def register_knowledge_tools(registry: ToolRegistry, retriever: Retriever) -> None:
    async def _search_knowledge(arguments: dict[str, Any], _session: Session) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        k = int(arguments.get("k", 3))
        hits = retriever.retrieve(query, k)
        if not hits:
            return ToolResult(content="No relevant knowledge found.")
        lines = [f"[{chunk.source}] {chunk.text}" for chunk in hits]
        return ToolResult(content="Knowledge:\n" + "\n".join(lines))

    registry.register(SEARCH_KNOWLEDGE_SPEC, _search_knowledge)
