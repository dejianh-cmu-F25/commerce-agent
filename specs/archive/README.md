# Archived specs

These features are **retired** from the active scope of the project, which is now
a closed-loop shopping agent (feature `046-closed-loop`, superseding `045`). They
are kept for traceability — the history of how the project got here — but they are
**not** maintained and the gate does not review them.

| Spec | Why archived |
| --- | --- |
| `002-web-experience` | superseded by `003-react-web-ui` (feature parity, React surface) |
| `009-cart-checkout` | cart/checkout is out of scope (no payments) |
| `011-evaluation` | superseded by `023-agent-evaluation` (the harness upgrade) |
| `010-merchant-agent` | the merchant agent is retired |
| `013-customer-memory` | cross-session memory is not in the 045 scope |
| `016-scenario-runner` | superseded by the two-layer evaluation harness |
| `017-metrics-dashboard` | not core to the shopping journey |
| `018-dense-retrieval` | superseded by the ESCI retrieval benchmark (planned) |
| `019-skills` | skills are not in the 045 scope |
| `021-chroma-vector-store` | the vector store is not core to the current design |
| `024-parameterized-cases` | superseded by the human-labeled corpora |
| `025-eval-report-view` | the report view is not core to the shopping journey |

## Restoring

`git mv specs/archive/<NNN>-<name> specs/<NNN>-<name>` and re-add the required
sections (see `.specify/templates/spec-template.md`). The code for some of these
features still exists under `app/` and can be re-enabled behind configuration.
