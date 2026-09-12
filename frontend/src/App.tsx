import { useChat } from "@ai-sdk/react";
import type { ToolUIPart } from "ai";
import { AlertCircleIcon, RotateCcwIcon } from "lucide-react";
import { Suspense, lazy, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { AgentChatTransport, type AgentUIMessage } from "@/lib/transport";
import { rehydrateMessages, type ServerMessage } from "@/lib/resume";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputProvider,
  PromptInputSubmit,
  PromptInputTextarea,
  usePromptInputController,
} from "@/components/ai-elements/prompt-input";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { BudgetMeter, type Budget } from "@/components/app/budget-meter";
import { CartCard } from "@/components/app/cart-card";
import { SourcesList } from "@/components/app/sources-list";
import { TraceViewer } from "@/components/app/trace-viewer";

// Tool steps pull in the syntax highlighter (shiki); load them on demand so the
// initial bundle stays small.
const ToolStep = lazy(() =>
  import("@/components/app/tool-step").then((m) => ({ default: m.ToolStep })),
);

const transport = new AgentChatTransport();

// One responsive column shared by the header, transcript, and composer so they
// stay aligned and scale with the window. Fluid: 92% on small screens, capped at
// 80rem (~1280px) for readable line length on large screens. `min()` never
// overflows. See docs/ui-conventions.md.
const CONTAINER = "mx-auto w-full max-w-[min(80rem,92%)]";

const SUGGESTIONS = [
  { label: "A tent under $250", prompt: "I need a tent under $250 for a weekend trip" },
  { label: "Cheapest camp stove", prompt: "What is the cheapest camp stove you have?" },
  { label: "Gear for a 2-day hike", prompt: "Help me put together gear for a 2-day hike" },
];

function latestBudget(messages: AgentUIMessage[]): Budget | null {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const parts = messages[i].parts;
    for (let j = parts.length - 1; j >= 0; j -= 1) {
      const part = parts[j];
      if (part.type === "data-budget") return part.data;
    }
  }
  return null;
}

function Chat() {
  const { messages, setMessages, sendMessage, status, stop, regenerate, error } =
    useChat<AgentUIMessage>({ transport });
  const controller = usePromptInputController();
  const budget = latestBudget(messages);
  const isEmpty = messages.length === 0;
  const [resuming, setResuming] = useState(() => transport.getSessionId() !== null);
  const [view, setView] = useState<"chat" | "traces">("chat");

  // Resume the conversation from the server log after a reload (feature 006).
  useEffect(() => {
    const sessionId = transport.getSessionId();
    if (!sessionId) return;
    let cancelled = false;
    fetch(`/sessions/${sessionId}`)
      .then(async (response) => {
        if (response.status === 404) {
          transport.reset();
          return null;
        }
        if (!response.ok) return null;
        return (await response.json()) as { messages: ServerMessage[] };
      })
      .then((data) => {
        if (!cancelled && data) setMessages(rehydrateMessages(data.messages));
      })
      .catch(() => {
        /* history load failed; keep the empty state (RD-1) */
      })
      .finally(() => {
        if (!cancelled) setResuming(false);
      });
    return () => {
      cancelled = true;
    };
  }, [setMessages]);

  function newChat() {
    transport.reset();
    setMessages([]);
  }

  return (
    <div className="flex h-dvh flex-col bg-background text-foreground">
      <header className="shrink-0 border-b">
        <div className={cn(CONTAINER, "flex items-center gap-3 px-4 py-3")}>
          <h1 className="text-sm font-semibold">Commerce Agent</h1>
          <span className="hidden text-xs text-muted-foreground sm:inline">
            ACME storefront · spec-driven demo
          </span>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-0.5 rounded-md border p-0.5">
              <button
                type="button"
                onClick={() => setView("chat")}
                className={cn(
                  "rounded px-2 py-0.5 text-xs",
                  view === "chat" ? "bg-accent text-foreground" : "text-muted-foreground",
                )}
              >
                Chat
              </button>
              <button
                type="button"
                onClick={() => setView("traces")}
                className={cn(
                  "rounded px-2 py-0.5 text-xs",
                  view === "traces" ? "bg-accent text-foreground" : "text-muted-foreground",
                )}
              >
                Traces
              </button>
            </div>
            <button
              type="button"
              onClick={newChat}
              className="rounded-md border px-2 py-1 text-xs text-muted-foreground hover:text-foreground"
            >
              New chat
            </button>
            <BudgetMeter budget={budget} />
          </div>
        </div>
      </header>

      {view === "traces" ? (
        <TraceViewer />
      ) : (
        <>
          <Conversation className="min-h-0 flex-1" aria-live="polite">
        <ConversationContent
          className={cn(CONTAINER, "gap-6", isEmpty && "min-h-full")}
        >
          {isEmpty ? (
            <ConversationEmptyState className="flex-1">
              {resuming ? (
                <p className="text-sm text-muted-foreground">Loading conversation…</p>
              ) : (
                <>
                  <h3 className="font-medium text-sm">Ask for something to get started.</h3>
                  <p className="text-sm text-muted-foreground">Try one of these:</p>
                  <Suggestions className="w-auto flex-wrap justify-center gap-2 whitespace-normal pt-2">
                    {SUGGESTIONS.map((s) => (
                      <Suggestion
                        key={s.label}
                        suggestion={s.label}
                        onClick={() => controller.textInput.setInput(s.prompt)}
                      />
                    ))}
                  </Suggestions>
                </>
              )}
            </ConversationEmptyState>
          ) : (
            messages.map((message) => (
              <Message
                key={message.id}
                from={message.role === "user" ? "user" : "assistant"}
              >
                <MessageContent>
                  {message.parts.map((part, index) => {
                    if (part.type === "text") {
                      return <MessageResponse key={index}>{part.text}</MessageResponse>;
                    }
                    if (part.type.startsWith("tool-")) {
                      return (
                        <Suspense key={index} fallback={null}>
                          <ToolStep part={part as ToolUIPart} />
                        </Suspense>
                      );
                    }
                    if (part.type === "data-sources") {
                      return <SourcesList key={index} items={part.data.items} />;
                    }
                    if (part.type === "data-cart") {
                      return (
                        <CartCard
                          key={index}
                          title="Cart"
                          items={part.data.items}
                          total={part.data.total}
                        />
                      );
                    }
                    if (part.type === "data-checkout") {
                      return (
                        <CartCard
                          key={index}
                          title="Checkout"
                          items={part.data.items}
                          total={part.data.total}
                          note="No payment is taken — this is a render only."
                        />
                      );
                    }
                    return null;
                  })}
                </MessageContent>
              </Message>
            ))
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {error ? (
        <div
          className={cn(
            CONTAINER,
            "mb-2 flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm",
          )}
        >
          <AlertCircleIcon className="size-4 shrink-0" />
          <span className="flex-1">{error.message || "Something went wrong."}</span>
          <button
            type="button"
            onClick={() => regenerate()}
            className="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs hover:bg-background"
          >
            <RotateCcwIcon className="size-3" /> Retry
          </button>
        </div>
      ) : null}

      <div className="shrink-0 border-t">
        <PromptInput
          onSubmit={(message) => sendMessage({ text: message.text })}
          className={cn(CONTAINER, "p-3")}
        >
          <PromptInputBody>
            <PromptInputTextarea placeholder="Ask for something, e.g. a tent under $250" />
          </PromptInputBody>
          <PromptInputFooter className="justify-end">
            <PromptInputSubmit status={status} onStop={stop} />
          </PromptInputFooter>
        </PromptInput>
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  return (
    <PromptInputProvider>
      <Chat />
    </PromptInputProvider>
  );
}
