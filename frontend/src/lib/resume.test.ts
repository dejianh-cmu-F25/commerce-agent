import { describe, expect, it } from "vitest";
import { rehydrateMessages } from "./resume";

describe("rehydrateMessages", () => {
  it("maps user and assistant text and skips tool messages", () => {
    const out = rehydrateMessages([
      { role: "user", content: "hi" },
      { role: "assistant", content: "hello" },
      { role: "tool", content: "{}", tool_call_id: "c1", name: "search_products" },
    ]);
    expect(out.map((m) => m.role)).toEqual(["user", "assistant"]);
    expect((out[0].parts[0] as { text: string }).text).toBe("hi");
  });

  it("skips assistant messages with empty content", () => {
    const out = rehydrateMessages([
      { role: "assistant", content: "" },
      { role: "assistant", content: "answer" },
    ]);
    expect(out).toHaveLength(1);
    expect((out[0].parts[0] as { text: string }).text).toBe("answer");
  });

  it("gives each message a unique id", () => {
    const out = rehydrateMessages([
      { role: "user", content: "a" },
      { role: "user", content: "b" },
    ]);
    expect(out[0].id).not.toBe(out[1].id);
  });
});
