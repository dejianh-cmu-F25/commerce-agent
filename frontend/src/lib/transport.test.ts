import { describe, expect, it } from "vitest";
import type { UIMessageChunk } from "ai";
import { mapEvent } from "./transport";

type Ctx = Parameters<typeof mapEvent>[1];
const ctx = (): Ctx => ({ textId: null, toolStacks: new Map() });

describe("mapEvent", () => {
  it("opens and streams text", () => {
    const c = ctx();
    const first = mapEvent({ type: "TextDelta", data: { text: "Hel" } }, c);
    const second = mapEvent({ type: "TextDelta", data: { text: "lo" } }, c);

    expect(first[0].type).toBe("text-start");
    expect(first[1]).toEqual({
      type: "text-delta",
      id: (first[0] as { id: string }).id,
      delta: "Hel",
    });
    // The same text id is reused; no second text-start.
    expect(second).toHaveLength(1);
    expect(second[0].type).toBe("text-delta");
  });

  it("pairs tool calls with results by name", () => {
    const c = ctx();
    const started = mapEvent(
      { type: "ToolCallStarted", data: { name: "search_products", arguments: { query: "tent" } } },
      c,
    );
    expect(started.map((chunk) => chunk.type)).toEqual([
      "tool-input-start",
      "tool-input-available",
    ]);
    const callId = (started[0] as { toolCallId: string }).toolCallId;

    const result = mapEvent(
      { type: "ToolResult", data: { name: "search_products", status: "ok", summary: "…" } },
      c,
    );
    expect(result[0].type).toBe("tool-output-available");
    expect((result[0] as { toolCallId: string }).toolCallId).toBe(callId);
  });

  it("maps the products component to a data-sources part", () => {
    const c = ctx();
    const chunks = mapEvent(
      {
        type: "UIComponent",
        data: {
          component: "products",
          payload: { items: [{ id: "P-101", title: "2-Person Tent", price: 189, in_stock: true }] },
        },
      },
      c,
    );
    expect(chunks[0].type).toBe("data-sources");
    expect((chunks[0] as { data: { items: unknown[] } }).data.items).toHaveLength(1);
  });

  it("maps usage to a data-budget part", () => {
    const c = ctx();
    const chunks = mapEvent(
      { type: "UsageReported", data: { spent_cny: 0.01, limit_cny: 10, remaining_cny: 9.99 } },
      c,
    );
    expect(chunks[0].type).toBe("data-budget");
    expect((chunks[0] as { data: { limit_cny: number } }).data.limit_cny).toBe(10);
  });

  it("maps errors and finishes the turn", () => {
    const c = ctx();
    mapEvent({ type: "TextDelta", data: { text: "hi" } }, c);
    const errored = mapEvent({ type: "ErrorEvent", data: { message: "boom" } }, c);
    expect(errored[0]).toEqual({ type: "error", errorText: "boom" });

    const end = mapEvent({ type: "TurnEnd", data: { reason: "stop" } }, c);
    expect(end.map((chunk: UIMessageChunk) => chunk.type)).toEqual(["text-end", "finish"]);
    expect(c.textId).toBeNull();
  });

  it("ignores unknown events", () => {
    expect(mapEvent({ type: "CartUpdate", data: {} }, ctx())).toEqual([]);
  });
});

describe("the closed-loop components reach the UI", () => {
  // Regression: the tools emitted `return_decision`, `returnable_items` and `reviews`
  // while this mapper only knew `return` - so the return decision card never rendered,
  // silently. A component the mapper does not know is a component nobody sees.
  const ui = (component: string, payload: Record<string, unknown>) =>
    mapEvent({ type: "UIComponent", data: { component, payload } }, ctx());

  it("maps return_decision, in all three shapes it is emitted", () => {
    const accepted = ui("return_decision", {
      order_id: "1006",
      decision: "eligible",
      cited_clauses: ["returns#window-default"],
      validated: true,
    });
    expect(accepted[0].type).toBe("data-return-decision");
    expect((accepted[0] as { data: { decision: string } }).data.decision).toBe("eligible");

    const refused = ui("return_decision", {
      order_id: "1006",
      decision: "eligible",
      validated: false,
      policy: "ineligible: delivered 45 days ago",
    });
    expect(refused[0].type).toBe("data-return-decision");

    const unreadable = ui("return_decision", {
      order_id: "1002",
      accessible: false,
      reason: "order belongs to another customer",
    });
    expect(unreadable[0].type).toBe("data-return-decision");
  });

  it("maps returnable_items and reviews when they carry items", () => {
    expect(ui("returnable_items", { items: [{ title: "Tent", quantity: 1 }] })[0].type).toBe(
      "data-returnable-items",
    );
    expect(ui("reviews", { items: [{ rating: 1, title: "Very tight", text: "…" }] })[0].type).toBe(
      "data-reviews",
    );
  });

  it("renders nothing for an empty list rather than an empty card", () => {
    expect(ui("returnable_items", { items: [] })).toHaveLength(0);
    expect(ui("reviews", { items: [] })).toHaveLength(0);
    // A component emitted without a payload (as returnable_items was) must not crash
    // the mapper either.
    expect(ui("returnable_items", {})).toHaveLength(0);
  });
});
