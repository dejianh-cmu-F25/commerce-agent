# Research: Web Experience

Phase 0 decisions and the alternatives weighed. Constitution references in
parentheses.

## D1. Markdown rendering + sanitizing

**Decision**: Vendor pinned `marked` (markdown → HTML) and `DOMPurify`
(sanitize) as committed files under `web/static/vendor/`, loaded with plain
`<script>` tags. Render through `DOMPurify.sanitize(marked.parse(text))`.

**Rationale**: Model output is untrusted (prompt injection, tool content) and
must never execute (WV-9). Both libraries are small, permissively licensed
(`marked` MIT; `DOMPurify` Apache-2.0 / MPL-2.0), and work with no build step
(P6, HR-9). Committing them keeps the app offline-reproducible in containers
(P8, DP-4).

**Alternatives considered**:
- *Hand-rolled markdown subset* — no dependency, but re-implements escaping and
  link handling, where the security risk is highest.
- *`markdown-it`* — comparable; `marked` is smaller and sufficient here.
- *CDN load* — rejected: breaks offline/container reproducibility and adds a
  runtime network dependency.

## D2. Keep vanilla JS + component registry

**Decision**: Keep the 001 surface (vanilla JS, `componentRegistry`) and add a
small explicit state machine (`idle → submitted → streaming → ready | error`).

**Rationale**: The demo's value is the harness, not the framework. A state
machine makes the UI states in the spec testable (WV-6) without a toolchain
(P6, HR-9).

**Alternatives considered**:
- *React + assistant-ui / AI Elements* — rich, but adds a build pipeline and a
  runtime framework for a single screen. Rejected (P6, HR-9).

## D3. Theming

**Decision**: Move styles to `web/static/styles.css`; define tokens as CSS custom
properties with a `prefers-color-scheme: light` override.

**Rationale**: Satisfies WV-8 with no JS and no theme toggle to persist.

**Alternatives considered**: single dark theme (rejected: WV-8); a manual toggle
with localStorage (rejected: extra state, not required).

## D4. Stop control

**Decision**: `Stop` aborts the client `fetch` via `AbortController` and finalizes
the current turn as `ready` with the partial reply retained. The server keeps
running its turn (no cancel endpoint).

**Rationale**: Immediate, honest UX with no new backend contract. The partial
reply is already in the DOM; the server's `TurnEnd` is simply not read.

**Alternatives considered**: a server-side cancel endpoint (rejected: new
contract and lifecycle for little user value in a demo).

## D5. Sources / provenance

**Decision**: Extend `ToolResult` with optional `component` + `payload`. When a
tool sets them, the loop emits a generic `UIComponent(component, payload)`. The
`search_products` tool sets `component="products"` with its items. The client's
existing `products` renderer displays them as the grounded sources.

**Rationale**: Keeps the loop generic (it forwards a tool-declared component, it
does not know product semantics) and finally exercises the `products` renderer
(WV-3). Provenance stays server-owned (P4).

**Alternatives considered**:
- *Parse `ToolResult.summary`* — rejected: it is truncated at 160 chars, so the
  JSON is often invalid.
- *New `Sources` event type* — rejected: `UIComponent` already exists for this;
  a new type would duplicate the mechanism.

## D6. Accessibility and motion

**Decision**: `aria-live="polite"` region for streamed text; focus rings via
`box-shadow`; Enter submits, Esc stops; inputs ≥ 16px; `prefers-reduced-motion`
disables non-essential animation; interaction transitions ≤ 200ms.

**Rationale**: WV-7 and the curated checklist in `docs/ui-conventions.md`.

## D7. Auto-scroll

**Decision**: Follow the stream only while the user is pinned to the bottom;
otherwise show a "scroll to bottom" button.

**Rationale**: Prevents the common "fighting the user" failure; matches popular
agent UIs.
