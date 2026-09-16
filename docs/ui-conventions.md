# Web UI Conventions

Guide for specifying, building, and reviewing the browser surface (constitution
WV-1..WV-9, HR-3). The surface is React 19 + Vite + Tailwind v4 + shadcn/ui +
Vercel AI Elements (feature 003); we take the *patterns* from popular agent
frontends and keep the harness (backend, event contract) framework-agnostic.

## Writing the UI part of a spec

Keep it **technology-agnostic and testable** — describe behavior, not CSS or
frameworks. A browser-visible spec includes, in addition to `## Web Acceptance`:

- **UI States** — one row per state: empty, loading/streaming, success, error,
  disabled. Define what the user sees and does in each. Happy-path-only is
  incomplete (WV-6).
- **Accessibility** — keyboard, focus, `aria-live` for streamed text,
  `prefers-reduced-motion`, labeled controls, ≥16px inputs (WV-7).
- **Responsive & Theme** — the app fills the viewport and the layout scales with
  the window; usable from 320px up; follows `prefers-color-scheme` (WV-8). See
  "Layout & responsive constraints" below.
- **Rendering Safety** — model/user markup is sanitized before it enters the DOM
  (WV-9).

The template lives at `.specify/templates/spec-template.md`.

## Patterns to borrow from popular agent frontends

Source material: Vercel AI Elements, assistant-ui, and the AI SDK UI status
model (`submitted → streaming → ready/error`). Adopt selectively:

- **Conversation / Thread** — role-labeled messages; auto-scroll with a
  "scroll to bottom" affordance when the user has scrolled up.
- **Message actions** — copy; later, edit / regenerate / branch.
- **Response rendering** — markdown subset (bold, lists, links, inline code),
  streamed with a caret; sanitize first.
- **Tool call as a step** — collapsible, with a status badge (running / ok /
  error) and the arguments/result; never dump raw JSON inline with prose.
- **Sources / provenance** — show what grounded the answer (P4).
- **Suggestion chips** — empty-state prompts that seed the first message.
- **Prompt input** — auto-resize, Enter submits, Send disabled while in flight,
  a Stop button while streaming.
- **Budget meter** — model spend; a progress bar appears only when a cap is configured (HR-12).
- **Error state** — inline message with Retry; never a silent failure.

## Layout & responsive constraints

The app is a full-viewport shell (header / transcript / composer). These are
binding for any browser-visible feature:

- **Fill the viewport.** The shell is `100dvh`; header and composer are fixed
  height; the transcript takes the remaining space and scrolls. `body` height
  equals the viewport at every size.
- **No page-level horizontal scroll** at ≥320px. Wide content (code, tables,
  suggestion rows) scrolls or wraps inside its own container.
- **Readable, scaling content column.** Header content, transcript, and composer
  share one container with a **fluid** width — `min(80rem, 92%)`: ~92% of the
  viewport on small screens, capped at 80rem on large ones for readable line
  length. No fixed breakpoint jumps; `min()` never overflows. They stay aligned.
- **Empty state fills and centers** in the transcript area, not top-aligned.
- **Re-flow on live resize** with no stuck widths, overlap, or overflow.

## Review checklist

Reviewer-owned. Mark an item only when verified.

### Interactivity & forms
- [ ] Input is wrapped in a `<form>`; Enter submits.
- [ ] Send is disabled while a request is in flight (no duplicate requests).
- [ ] Inputs disable `spellcheck`/`autocomplete` where appropriate.
- [ ] Clicking a label focuses its input; no dead areas in lists.

### Streaming & agent UX
- [ ] Status is visible: idle / submitted / streaming / ready / error.
- [ ] Streamed text appears progressively; a Stop control is available.
- [ ] Tool calls render as distinct steps with a status, not inline with prose.
- [ ] Errors surface inline with a Retry path.
- [ ] Auto-scroll does not fight the user; a "scroll to bottom" control exists.

### Typography
- [ ] `-webkit-font-smoothing: antialiased`; weights below 400 avoided.
- [ ] Tabular figures for timers/counters (`font-variant-numeric: tabular-nums`).
- [ ] Font weight does not change on hover (no layout shift).

### Motion
- [ ] Interaction animations are ≤ 200ms; scale changes are subtle (≈0.96–0.98).
- [ ] Frequent, low-novelty actions avoid extraneous animation.
- [ ] Looping animation pauses when off-screen.

### Touch
- [ ] Hover styles gated behind `@media (hover: hover)`.
- [ ] Input font size ≥ 16px (prevents iOS zoom).
- [ ] `-webkit-tap-highlight-color` replaced with an intentional state.

### Accessibility
- [ ] Keyboard operable; visible focus ring (box-shadow, not bare outline).
- [ ] Streamed content announced with `aria-live="polite"`.
- [ ] Icon-only controls have `aria-label`.
- [ ] Images use `<img>`; decorative elements set `pointer-events: none`.
- [ ] Motion respects `prefers-reduced-motion`.

### Feedback & empty states
- [ ] Empty state prompts the first action (suggestions or templates).
- [ ] Feedback is shown relative to its trigger (inline, not a global toast).
- [ ] Theme follows `prefers-color-scheme`; a favicon is present.

### Layout & responsive
- [ ] The shell fills the viewport (`body` height == window height).
- [ ] No page-level horizontal scroll at 320–1920px.
- [ ] Header, transcript, and composer share one aligned column with a fluid width
      (`min(80rem, 92%)`): fills small screens, capped for readability on large ones.
- [ ] Empty state fills and is vertically centered.
- [ ] Suggestion rows wrap (or scroll inside their own container) on narrow screens.
- [ ] Live window resize re-flows with no stuck widths or overlap.

## Rendering safety (WV-9)

Model output is untrusted: it is influenced by user text and tool results. The
React surface renders markdown through Streamdown (`MessageResponse`), which
sanitizes; links get `rel="noopener noreferrer"`. If you add a raw-HTML renderer,
sanitize first (e.g., DOMPurify). Never assign model-derived strings to
`innerHTML` without sanitizing.

## Sources

- Rauno Freiberg, *Web Interface Guidelines* — https://interfaces.rauno.me
- Vercel, *AI Elements* — https://ai-sdk.dev/elements
- assistant-ui docs — https://www.assistant-ui.com/docs
- Vercel, *AI SDK UI* (useChat status model) — https://ai-sdk.dev/docs/ai-sdk-ui/overview

## Tool components reach the transcript by name (feature 046)

A tool result may declare a `component` plus a `payload`; the loop forwards both, and
`frontend/src/lib/transport.ts` maps the declared name onto a typed data part that
`App.tsx` renders. Two rules make that contract safe:

1. **A name the mapper does not know is a card nobody sees.** This is not hypothetical:
   the closed-loop tools emit `return_decision`, `returnable_items` and `reviews` while
   the mapper only knew `return`, so the return-decision card - the customer's view of
   both the proposal and the harness's verdict on it - never rendered, and nothing
   failed. Every new component name needs a mapping, a render branch and a mapper test.
2. **A component with no payload renders nothing.** `list_returnable_items` emitted its
   component without a payload. The mapper now skips an empty list rather than drawing
   an empty card, and `transport.test.ts` pins that.

The components the transcript renders today: `products` (sources list), `cart`,
`checkout`, `orders`, `order`, `return` (legacy), `return_decision`, `returnable_items`,
`reviews`.

Render-level tests would need a DOM environment (jsdom + testing-library); the project
deliberately keeps its frontend tests to the mapper and the stream contract, which is
where this failure mode actually lives.
