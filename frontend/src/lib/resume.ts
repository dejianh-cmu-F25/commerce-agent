import type { AgentUIMessage } from "./transport";

export type ServerMessage = {
  role: "user" | "assistant" | "tool" | "system";
  content: string;
  tool_calls?: { id: string; name: string; arguments: string }[];
  tool_call_id?: string;
  name?: string;
};

// Map the server's derived messages (GET /sessions/{id}) back to UI messages.
// Text-only: tool messages are skipped (see spec 006 assumptions).
export function rehydrateMessages(messages: ServerMessage[]): AgentUIMessage[] {
  const out: AgentUIMessage[] = [];
  for (const message of messages) {
    if (message.role === "user") {
      out.push({
        id: crypto.randomUUID(),
        role: "user",
        parts: [{ type: "text", text: message.content }],
      } as AgentUIMessage);
    } else if (message.role === "assistant" && message.content.trim() !== "") {
      out.push({
        id: crypto.randomUUID(),
        role: "assistant",
        parts: [{ type: "text", text: message.content }],
      } as AgentUIMessage);
    }
  }
  return out;
}
