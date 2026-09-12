// Chat client for the commerce agent.
//
// One explicit turn state machine (idle -> submitted -> streaming -> ready/error)
// drives the UI (WV-6). Markdown is rendered through marked + DOMPurify so no
// model-derived markup can execute (WV-9). New component types register in
// componentRegistry without touching the stream loop (WV-3).

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendEl = document.getElementById("send");
const stopEl = document.getElementById("stop");
const statusEl = document.getElementById("status");
const composerEl = document.getElementById("composer");
const toBottomEl = document.getElementById("to-bottom");
const budgetEl = document.getElementById("budget");
const budgetTextEl = document.getElementById("budget-text");
const budgetFillEl = document.getElementById("budget-fill");
const budgetBarEl = budgetEl.querySelector(".bar");

const STATUS_LABEL = {
  idle: "",
  submitted: "Thinking…",
  streaming: "Responding…",
  ready: "",
  error: "",
};

const SUGGESTIONS = [
  { label: "A tent under $250", prompt: "I need a tent under $250 for a weekend trip" },
  { label: "Cheapest camp stove", prompt: "What is the cheapest camp stove you have?" },
  { label: "Gear for a 2-day hike", prompt: "Help me put together gear for a 2-day hike" },
];

const state = {
  sessionId: null,
  status: "idle",
  controller: null,
  current: null,
  lastUserText: "",
  spent: 0,
  limit: 0,
};

const isBusy = () => state.status === "submitted" || state.status === "streaming";

// --- Scrolling: follow only while the user is at the bottom (D7) ---

let pinned = true;
function atBottom() {
  return messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 48;
}
messagesEl.addEventListener("scroll", () => {
  pinned = atBottom();
  toBottomEl.hidden = pinned;
});
function scrollIfPinned() {
  if (pinned) messagesEl.scrollTop = messagesEl.scrollHeight;
}
toBottomEl.addEventListener("click", () => {
  pinned = true;
  toBottomEl.hidden = true;
  messagesEl.scrollTop = messagesEl.scrollHeight;
});

// --- Safe markdown (WV-9) ---

function renderMarkdown(text) {
  const html = marked.parse(text, { breaks: true, gfm: true });
  const clean = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
  const holder = document.createElement("div");
  holder.innerHTML = clean;
  holder.querySelectorAll("a").forEach((a) => {
    a.setAttribute("target", "_blank");
    a.setAttribute("rel", "noopener noreferrer");
  });
  return holder.innerHTML;
}

function makeCaret() {
  const caret = document.createElement("span");
  caret.className = "caret";
  caret.setAttribute("aria-hidden", "true");
  return caret;
}

// --- Component registry (WV-3) ---

const componentRegistry = {
  products(payload, handle) {
    const items = payload.items || [];
    handle.items = items;
    if (!items.length) return;
    handle.sources.innerHTML = "";
    const label = document.createElement("div");
    label.className = "label";
    label.textContent = "Sources";
    const card = document.createElement("div");
    card.className = "card";
    for (const item of items) {
      const row = document.createElement("div");
      row.className = "row";
      const title = document.createElement("span");
      title.className = "title";
      title.textContent = item.title;
      const price = document.createElement("span");
      price.className = "price";
      price.textContent = `$${Number(item.price).toFixed(2)}`;
      row.append(title, price);
      if (!item.in_stock) {
        const oos = document.createElement("span");
        oos.className = "oos";
        oos.textContent = "out of stock";
        row.append(oos);
      }
      card.append(row);
    }
    handle.sources.append(label, card);
  },
};

function renderComponent(component, payload) {
  const renderer = componentRegistry[component];
  if (renderer && state.current) {
    renderer(payload, state.current);
  } else if (state.current) {
    addStepNotice(state.current, `[ui] ${component} (no renderer)`);
  }
}

function addStepNotice(handle, text) {
  const notice = document.createElement("div");
  notice.className = "step";
  notice.textContent = text;
  handle.steps.append(notice);
}

// --- Message rendering ---

function addUserMessage(text) {
  messagesEl.querySelector(".empty")?.remove();
  const wrap = document.createElement("div");
  wrap.className = "msg user";
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = "You";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrap.append(meta, bubble);
  messagesEl.append(wrap);
  scrollIfPinned();
}

function addAgentMessage() {
  const wrap = document.createElement("div");
  wrap.className = "msg agent";
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = "Agent";
  const steps = document.createElement("div");
  steps.className = "steps";
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const content = document.createElement("div");
  content.className = "md";
  bubble.append(content);
  const sources = document.createElement("div");
  sources.className = "sources";
  const actions = document.createElement("div");
  actions.className = "actions";
  wrap.append(meta, steps, bubble, sources, actions);
  messagesEl.append(wrap);
  const handle = { wrap, steps, bubble, content, sources, actions, raw: "", items: [], stepList: [] };
  state.current = handle;
  renderAgentText(handle);
  scrollIfPinned();
  return handle;
}

function renderAgentText(handle) {
  if (handle.raw) {
    handle.content.innerHTML = renderMarkdown(handle.raw);
  } else {
    handle.content.innerHTML = '<span class="placeholder">…</span>';
  }
  if (isBusy() && handle.raw) handle.content.append(makeCaret());
}

function addActions(handle) {
  if (handle.actions.dataset.done) return;
  handle.actions.dataset.done = "1";
  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = "Copy";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(handle.raw);
      copy.textContent = "Copied";
      setTimeout(() => (copy.textContent = "Copy"), 1200);
    } catch {
      copy.textContent = "Copy failed";
      setTimeout(() => (copy.textContent = "Copy"), 1200);
    }
  });
  handle.actions.append(copy);
}

function addStep(name, args) {
  const handle = state.current;
  if (!handle) return;
  const details = document.createElement("details");
  details.className = "step";
  details.open = true;
  const summary = document.createElement("summary");
  const nm = document.createElement("span");
  nm.className = "name";
  nm.textContent = name;
  const ar = document.createElement("span");
  ar.className = "args";
  ar.textContent = JSON.stringify(args || {});
  const badge = document.createElement("span");
  badge.className = "badge running";
  badge.textContent = "running";
  summary.append(nm, ar, badge);
  const body = document.createElement("div");
  body.className = "body";
  details.append(summary, body);
  handle.steps.append(details);
  handle.stepList.push({ name, badge, body });
  scrollIfPinned();
}

function updateStep(name, status, summary) {
  const handle = state.current;
  if (!handle) return;
  const match = [...handle.stepList]
    .reverse()
    .find((s) => s.name === name && s.badge.classList.contains("running"));
  const target = match || handle.stepList[handle.stepList.length - 1];
  if (!target) return;
  target.badge.className = `badge ${status}`;
  target.badge.textContent = status;
  if (summary) target.body.textContent = summary;
}

function showError(message) {
  const handle = state.current || addAgentMessage();
  handle.wrap.querySelector(".error")?.remove();
  const box = document.createElement("div");
  box.className = "error";
  const grow = document.createElement("span");
  grow.className = "grow";
  grow.textContent = message || "Something went wrong.";
  const retry = document.createElement("button");
  retry.type = "button";
  retry.textContent = "Retry";
  retry.addEventListener("click", () => {
    box.remove();
    if (state.lastUserText) send(state.lastUserText);
  });
  box.append(grow, retry);
  handle.wrap.append(box);
  setStatus("error");
  scrollIfPinned();
}

// --- Status + controls (WV-6) ---

function setStatus(next) {
  state.status = next;
  statusEl.textContent = STATUS_LABEL[next] || "";
  if (state.current) renderAgentText(state.current);
  updateControls();
}

function updateControls() {
  stopEl.hidden = !isBusy();
  sendEl.disabled = isBusy() || inputEl.value.trim() === "";
}

// --- Budget meter (HR-12) ---

function updateBudget(spent, limit) {
  state.spent = Number(spent) || 0;
  state.limit = Number(limit) || 0;
  const pct = state.limit ? Math.min(100, (state.spent / state.limit) * 100) : 0;
  budgetTextEl.textContent = `budget: ¥${state.spent.toFixed(4)} / ¥${state.limit.toFixed(2)}`;
  budgetFillEl.style.width = `${pct}%`;
  budgetBarEl.setAttribute("aria-valuenow", String(Math.round(pct)));
  budgetEl.classList.toggle("over", pct >= 100);
}

// --- Empty state ---

function renderEmptyState() {
  if (messagesEl.querySelector(".msg")) return;
  const box = document.createElement("div");
  box.className = "empty";
  const p = document.createElement("p");
  p.textContent = "Ask for something to get started.";
  const wrap = document.createElement("div");
  wrap.className = "suggestions";
  for (const s of SUGGESTIONS) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = s.label;
    chip.addEventListener("click", () => {
      inputEl.value = s.prompt;
      updateControls();
      inputEl.focus();
    });
    wrap.append(chip);
  }
  box.append(p, wrap);
  messagesEl.append(box);
}

// --- SSE handling ---

function handleEvent(event) {
  const { type, data } = event;
  switch (type) {
    case "SessionStarted":
      state.sessionId = data.session_id;
      break;
    case "TurnStart":
      setStatus("submitted");
      break;
    case "TextDelta":
      if (state.current) {
        state.current.raw += data.text;
        renderAgentText(state.current);
      }
      if (state.status !== "streaming") setStatus("streaming");
      scrollIfPinned();
      break;
    case "ToolCallStarted":
      addStep(data.name, data.arguments);
      break;
    case "ToolResult":
      updateStep(data.name, data.status, data.summary);
      break;
    case "UIComponent":
      renderComponent(data.component, data.payload);
      break;
    case "UsageReported":
      updateBudget(data.spent_cny, data.limit_cny);
      break;
    case "BudgetExceeded":
      showError(`Budget limit reached: ¥${data.spent_cny} / ¥${data.limit_cny}`);
      break;
    case "ErrorEvent":
      showError(data.message);
      break;
    case "TurnEnd":
      setStatus(state.status === "error" ? "error" : "ready");
      finalizeCurrent();
      break;
    default:
      break;
  }
}

function finalizeCurrent() {
  const handle = state.current;
  if (!handle) return;
  renderAgentText(handle);
  addActions(handle);
}

async function readStream(body) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    // sse_starlette separates events with CRLF; normalize to LF before splitting.
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
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
}

// --- Send / stop / retry ---

async function send(text) {
  const message = (text ?? inputEl.value).trim();
  if (!message || isBusy()) return;
  inputEl.value = "";
  state.lastUserText = message;
  addUserMessage(message);
  addAgentMessage();
  state.controller = new AbortController();
  setStatus("submitted");
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: state.sessionId }),
      signal: state.controller.signal,
    });
    if (!response.ok || !response.body) throw new Error(`HTTP ${response.status}`);
    await readStream(response.body);
    if (state.status !== "error") setStatus("ready");
    finalizeCurrent();
  } catch (err) {
    if (err.name === "AbortError") {
      setStatus("ready");
      finalizeCurrent();
    } else {
      showError(`Connection error: ${err.message}`);
    }
  } finally {
    state.controller = null;
    updateControls();
    scrollIfPinned();
    inputEl.focus();
  }
}

function stop() {
  if (state.controller) state.controller.abort();
}

// --- Wiring ---

composerEl.addEventListener("submit", (e) => {
  e.preventDefault();
  send();
});
inputEl.addEventListener("input", updateControls);
stopEl.addEventListener("click", stop);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && isBusy()) stop();
});

renderEmptyState();
updateControls();
inputEl.focus();
