# Web UI Conventions

Guide for specifying, building, and reviewing the browser surface (constitution
WV-1..WV-9, HR-3). Borrowed patterns, not frameworks: this project stays
zero-build vanilla JS (P6, HR-9), so we take the *ideas* from popular agent
frontends and implement them with small, dependency-light components.

## Writing the UI part of a spec

Keep it **technology-agnostic and testable** — describe behavior, not CSS or
frameworks. A browser-visible spec includes, in addition to `## Web Acceptance`:

- **UI States** — one row per state: empty, loading/streaming, success, error,
  disabled. Define what the user sees and does in each. Happy-path-only is
  incomplete (WV-6).
- **Accessibility** — keyboard, focus, `aria-live` for streamed text,
  `prefers-reduced-motion`, labeled controls, ≥16px inputs (WV-7).
- **Responsive & Theme** — usable at 375px and desktop; follows
  `prefers-color-scheme` (WV-8).
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
- **Budget meter** — spend vs limit as a progress bar (HR-12).
- **Error state** — inline message with Retry; never a silent failure.

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

## Rendering safety (WV-9)

Model output is untrusted: it is influenced by user text and tool results. When
rendering markdown to HTML, always sanitize (e.g., vendored `marked` +
`DOMPurify`) and set `rel="noopener noreferrer"` on links. Never assign
model-derived strings to `innerHTML` without sanitizing.

## Sources

- Rauno Freiberg, *Web Interface Guidelines* — https://interfaces.rauno.me
- Vercel, *AI Elements* — https://ai-sdk.dev/elements
- assistant-ui docs — https://www.assistant-ui.com/docs
- Vercel, *AI SDK UI* (useChat status model) — https://ai-sdk.dev/docs/ai-sdk-ui/overview
