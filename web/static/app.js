// Chat client: POST /chat and render the SSE event stream.
// The component registry maps a UI component type to a renderer; new feature
// components register here without touching the chat loop (WV-3).

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendEl = document.getElementById("send");
const budgetEl = document.getElementById("budget");

function setBudget(spent, limit) {
  budgetEl.textContent = `budget: ¥${Number(spent).toFixed(4)} / ¥${Number(limit).toFixed(2)}`;
}

let sessionId = null;
let currentBubble = null;

function addMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = role === "user" ? "You" : "Agent";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text || "";
  wrap.append(meta, bubble);
  messagesEl.append(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function addToolLine(text) {
  const el = document.createElement("div");
  el.className = "tool";
  el.textContent = text;
  (currentBubble || messagesEl).append(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// --- Component registry (WV-3) ---

const componentRegistry = {
  products(payload, container) {
    const card = document.createElement("div");
    card.className = "card";
    for (const item of payload.items || []) {
      const row = document.createElement("div");
      row.className = "row";
      const name = document.createElement("span");
      name.textContent = item.title;
      const price = document.createElement("span");
      price.className = "price";
      price.textContent = `$${Number(item.price).toFixed(2)}`;
      row.append(name, price);
      if (!item.in_stock) {
        const oos = document.createElement("span");
        oos.className = "oos";
        oos.textContent = "out of stock";
        row.append(oos);
      }
      card.append(row);
    }
    container.append(card);
  },
};

function renderComponent(component, payload) {
  const renderer = componentRegistry[component];
  if (renderer) {
    renderer(payload, currentBubble || messagesEl);
  } else {
    addToolLine(`[ui] ${component} (no renderer)`);
  }
}

// --- SSE handling ---

function handleEvent(event) {
  const { type, data } = event;
  switch (type) {
    case "SessionStarted":
      sessionId = data.session_id;
      break;
    case "TextDelta":
      if (currentBubble) currentBubble.textContent += data.text;
      messagesEl.scrollTop = messagesEl.scrollHeight;
      break;
    case "ToolCallStarted":
      addToolLine(`→ ${data.name} ${JSON.stringify(data.arguments)}`);
      break;
    case "ToolResult":
      addToolLine(`← ${data.name} [${data.status}]`);
      break;
    case "UIComponent":
      renderComponent(data.component, data.payload);
      break;
    case "UsageReported":
      setBudget(data.spent_cny, data.limit_cny);
      break;
    case "BudgetExceeded":
      addToolLine(`budget limit reached: ¥${data.spent_cny} / ¥${data.limit_cny}`);
      break;
    case "ErrorEvent":
      addToolLine(`error: ${data.message}`);
      break;
    default:
      break;
  }
}

async function send() {
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  sendEl.disabled = true;
  addMessage("user", text);
  currentBubble = addMessage("agent", "");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop();
      for (const chunk of chunks) {
        const line = chunk.split("\n").find((l) => l.startsWith("data:"));
        if (!line) continue;
        try {
          handleEvent(JSON.parse(line.slice(5).trim()));
        } catch (err) {
          console.error("bad event", chunk, err);
        }
      }
    }
  } catch (err) {
    addToolLine(`connection error: ${err}`);
  } finally {
    sendEl.disabled = false;
    currentBubble = null;
    inputEl.focus();
  }
}

sendEl.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") send();
});
inputEl.focus();
