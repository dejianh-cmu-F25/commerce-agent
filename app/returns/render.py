"""Render the policy SoT into a human/model-readable prose document (046).

The prose corpus is a **build artifact**: it is generated from
``config/policies/amazon.yaml`` so the two can never drift. Do not hand-edit the
output; regenerate with ``python -m app.returns.render``.
"""

from __future__ import annotations

from app.returns.amazon_policy import AmazonPolicy, load_amazon_policy


def render_policy(policy: AmazonPolicy, version: str | None = None) -> str:
    name = version or policy.active_version
    spec = policy.version(name)
    source = str(spec.get("source", ""))
    src = policy.sources.get(source, {})
    lines = [
        f"# Amazon return policy ({name})",
        "",
        "> Derived from `config/policies/amazon.yaml` (single source of truth).",
        "> Do not edit by hand; regenerate with `python -m app.returns.render`.",
        "",
    ]
    if src:
        lines += [
            f"Source: [{source}]({src.get('url', '')}) — retrieved {src.get('retrieved_at', '')}.",
            "",
        ]
    for clause in policy.clauses(name):
        lines.append(f"## {clause.id}")
        lines.append("")
        lines.append(clause.paraphrase)
        lines.append("")
        if clause.rules:
            rules = ", ".join(f"`{key}={value}`" for key, value in clause.rules.items())
            lines.append(f"Rules: {rules}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    from pathlib import Path

    policy = load_amazon_policy()
    # The active version is what the model retrieves; superseded versions stay in
    # the SoT only (the engine's concern) and are never rendered into the corpus.
    path = Path("config/knowledge/amazon-returns.md")
    path.write_text(render_policy(policy, policy.active_version))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
