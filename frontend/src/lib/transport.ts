import type { ChatTransport, UIMessage, UIMessageChunk } from "ai";
import { getCustomerId } from "@/lib/identity";

export type Source = {
  id: string;
  title: string;
  price: number;
  in_stock: boolean;
};

export type CartItem = {
  product_id: string;
  title: string;
  quantity: number;
  unit_price: number;
  line_total: number;
};

export type CartData = { items: CartItem[]; total: number };
export type CheckoutData = { items: CartItem[]; total: number; charged: boolean };

// Custom data parts carried alongside the message (rendered by our components).
export type AgentDataTypes = {
  sources: { items: Source[] };
  budget: { spent_cny: number; limit_cny: number; remaining_cny: number };
  cart: CartData;
  checkout: CheckoutData;
};

export type AgentUIMessage = UIMessage<unknown, AgentDataTypes>;

type WireEvent = { type: string; data: Record<string, unknown> };

type Ctx = {
  textId: string | null;
  toolStacks: Map<string, string[]>;
};

const asString = (v: unknown, fallback = ""): string => (typeof v === "string" ? v : fallback);
const asNumber = (v: unknown): number => (typeof v === "number" ? v : Number(v ?? 0));

// The session id is kept in browser storage so a reload can resume (feature 006).
const SESSION_KEY = "commerce-agent.session";

function readStoredSession(): string | null {
  try {
    return window.localStorage.getItem(SESSION_KEY);
  } catch {
    return null; // storage unavailable (e.g. private mode)
  }
}

function writeStoredSession(id: string | null): void {
  try {
    if (id) window.localStorage.setItem(SESSION_KEY, id);
    else window.localStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore: behave as a fresh session */
  }
}

// Translate one backend AgentEvent into zero or more AI SDK UI message chunks.
export function mapEvent(event: WireEvent, ctx: Ctx): UIMessageChunk[] {
  const out: UIMessageChunk[] = [];
  switch (event.type) {
    case "TurnStart":
      out.push({ type: "start" });
      break;
    case "TextDelta": {
      if (!ctx.textId) {
        ctx.textId = crypto.randomUUID();
        out.push({ type: "text-start", id: ctx.textId });
      }
      out.push({ type: "text-delta", id: ctx.textId, delta: asString(event.data.text) });
      break;
    }
    case "ToolCallStarted": {
      const toolCallId = crypto.randomUUID();
      const name = asString(event.data.name, "tool");
      const stack = ctx.toolStacks.get(name) ?? [];
      stack.push(toolCallId);
      ctx.toolStacks.set(name, stack);
      out.push({ type: "tool-input-start", toolCallId, toolName: name });
      out.push({
        type: "tool-input-available",
        toolCallId,
        toolName: name,
        input: event.data.arguments ?? {},
      });
      break;
    }
    case "ToolResult": {
      const name = asString(event.data.name, "tool");
      const stack = ctx.toolStacks.get(name) ?? [];
      const toolCallId = stack.pop() ?? crypto.randomUUID();
      out.push({
        type: "tool-output-available",
        toolCallId,
        output: { status: asString(event.data.status, "ok"), summary: asString(event.data.summary) },
      });
      break;
    }
    case "UIComponent": {
      const component = event.data.component;
      const payload = (event.data.payload ?? {}) as Record<string, unknown>;
      if (component === "products") {
        out.push({ type: "data-sources", data: { items: (payload.items as Source[]) ?? [] } });
      } else if (component === "cart") {
        out.push({ type: "data-cart", data: payload as unknown as CartData });
      } else if (component === "checkout") {
        out.push({ type: "data-checkout", data: payload as unknown as CheckoutData });
      }
      break;
    }
    case "UsageReported":
      out.push({
        type: "data-budget",
        data: {
          spent_cny: asNumber(event.data.spent_cny),
          limit_cny: asNumber(event.data.limit_cny),
          remaining_cny: asNumber(event.data.remaining_cny),
        },
      });
      break;
    case "BudgetExceeded":
      out.push({
        type: "error",
        errorText: `Budget limit reached: ¥${asNumber(event.data.spent_cny)} / ¥${asNumber(event.data.limit_cny)}`,
      });
      break;
    case "ErrorEvent":
      out.push({ type: "error", errorText: asString(event.data.message, "Unknown error") });
      break;
    case "TurnEnd":
      if (ctx.textId) {
        out.push({ type: "text-end", id: ctx.textId });
        ctx.textId = null;
      }
      out.push({ type: "finish" });
      break;
    default:
      break;
  }
  return out;
}

// Adapts the backend's SSE event stream (POST /chat) to the AI SDK transport
// contract, so `useChat` drives status/stop/regenerate and AI Elements renders.
export class AgentChatTransport implements ChatTransport<AgentUIMessage> {
  private sessionId: string | null = readStoredSession();

  getSessionId(): string | null {
    return this.sessionId;
  }

  reset(): void {
    this.sessionId = null;
    writeStoredSession(null);
  }

  async sendMessages(
    options: Parameters<ChatTransport<AgentUIMessage>["sendMessages"]>[0],
  ): Promise<ReadableStream<UIMessageChunk>> {
    const lastUser = [...options.messages].reverse().find((m) => m.role === "user");
    const text =
      lastUser?.parts
        .filter((p): p is { type: "text"; text: string } => p.type === "text")
        .map((p) => p.text)
        .join("") ?? "";
    return this.stream(text, options.abortSignal);
  }

  async reconnectToStream(): Promise<ReadableStream<UIMessageChunk> | null> {
    return null;
  }

  private async stream(
    message: string,
    abortSignal?: AbortSignal,
  ): Promise<ReadableStream<UIMessageChunk>> {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: this.sessionId,
        customer_id: getCustomerId(),
      }),
      signal: abortSignal,
    });
    if (!response.ok || !response.body) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const ctx: Ctx = { textId: null, toolStacks: new Map() };
    let buffer = "";

    return new ReadableStream<UIMessageChunk>({
      start: async (controller) => {
        try {
          for (;;) {
            const { value, done } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
            const blocks = buffer.split("\n\n");
            buffer = blocks.pop() ?? "";
            for (const block of blocks) {
              const line = block.split("\n").find((l) => l.startsWith("data:"));
              if (!line) continue;
              const event = JSON.parse(line.slice(5).trim()) as WireEvent;
              if (event.type === "SessionStarted") {
                this.sessionId = asString(event.data.session_id) || null;
                writeStoredSession(this.sessionId);
                continue;
              }
              for (const chunk of mapEvent(event, ctx)) controller.enqueue(chunk);
            }
          }
          controller.close();
        } catch (err) {
          controller.error(err);
        }
      },
      cancel: () => {
        reader.cancel().catch(() => {});
      },
    });
  }
}
