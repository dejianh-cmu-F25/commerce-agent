import { describe, expect, it } from "vitest";
import { buildSpanTree, formatDuration, type Span } from "./traces";

function span(partial: Partial<Span> & Pick<Span, "span_id">): Span {
  return {
    trace_id: "t",
    parent_id: null,
    name: "turn",
    start_ms: 0,
    end_ms: 1,
    status: "ok",
    attributes: {},
    ...partial,
  };
}

describe("formatDuration", () => {
  it("uses ms below a second and seconds above", () => {
    expect(formatDuration(12.4)).toBe("12 ms");
    expect(formatDuration(1500)).toBe("1.5 s");
  });

  it("handles invalid input", () => {
    expect(formatDuration(Number.NaN)).toBe("—");
    expect(formatDuration(-1)).toBe("—");
  });
});

describe("buildSpanTree", () => {
  it("nests children under their parent and orders by start time", () => {
    const tree = buildSpanTree([
      span({ span_id: "turn", parent_id: null, start_ms: 0, end_ms: 10 }),
      span({ span_id: "tool", parent_id: "turn", name: "tool", start_ms: 5, end_ms: 9 }),
      span({ span_id: "llm", parent_id: "turn", name: "llm", start_ms: 1, end_ms: 5 }),
    ]);

    expect(tree).toHaveLength(1);
    expect(tree[0].span.span_id).toBe("turn");
    expect(tree[0].children.map((c) => c.span.span_id)).toEqual(["llm", "tool"]);
    expect(tree[0].children[0].depth).toBe(1);
  });

  it("treats a span with an unknown parent as a root", () => {
    const tree = buildSpanTree([span({ span_id: "orphan", parent_id: "missing" })]);
    expect(tree.map((n) => n.span.span_id)).toEqual(["orphan"]);
  });
});
