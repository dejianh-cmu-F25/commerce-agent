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
