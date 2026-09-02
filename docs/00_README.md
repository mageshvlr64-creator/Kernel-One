# Sovereign AI Workbench (SIH26176) — Documentation Set

This `docs/` tree is the complete specification for the Sovereign AI Workbench: a locally-hosted,
sovereignty-first AI workbench that plans and executes multi-step agentic tasks — document
Q&A, spreadsheet analysis, coding, report generation — entirely on infrastructure the
operator controls, with every model call, tool call, and file touch attributable and
auditable.

## How this documentation set is organized

| Directory | What it contains |
|---|---|
| `docs/` (root) | Product vision, scope, requirements, architecture summary, build order, and the rules that govern how this whole tree is written and kept in sync with code. |
| `architecture/` | Cross-cutting structural views: boundaries, trust zones, deployment topologies. |
| `domain/` | The core entities of the system (user, document, agent, task, execution, evidence, ...) independent of any one feature. |
| `schemas/` | The exact on-disk/on-wire shape of every persisted or transmitted structure. |
| `api/` | The HTTP/WebSocket contract, endpoint by endpoint. |
| `runtime/` | State machines, lifecycles, retry/timeout/concurrency rules. |
| `features/` | The 26 feature groups that make up the product, each fully specified per file using the 30-section standard in `13_DEVELOPER_RULES.md`. |
| `ui/` | Screens, panels, and UI states. |
| `workflows/` | End-to-end user scenarios that cross multiple features. |
| `security/` | Threat model and per-threat mitigations. |
| `failures/` | Every named failure mode and how the system responds to it. |
| `testing/` | Test strategy per subsystem. |
| `benchmarks/` | How local models are scored for the router. |
| `deployment/` | How the system is installed and run in each network mode. |
| `operations/` | Day-to-day operator procedures. |
| `performance/` | Latency/resource budgets. |
| `demo/` | The scripted jury/demo walkthrough. |
| `industrial/` | Domain-specific intelligence built on the core platform. |
| `later/` | Explicitly out-of-scope V2+ ideas, kept so they aren't accidentally built early. |
| `integrations/` | Contracts with third-party components (vLLM, Ollama, PostgreSQL, ...). |
| `reference/` | Lookup tables other documents point to instead of repeating. |

## Reading order for a new contributor (human or AI)

1. `00_README.md` (this file)
2. `01_PRODUCT_VISION.md`
3. `02_SCOPE_AND_NON_GOALS.md`
4. `04_SYSTEM_ARCHITECTURE.md`
5. `13_DEVELOPER_RULES.md`
6. `14_AI_IMPLEMENTATION_PROTOCOL.md`
7. The specific `features/<group>/` directory relevant to the task at hand

## Ground rules

- **Docs are the source of truth.** If code disagrees with a doc, that is a bug in one of the
  two — fix the disagreement, don't just pick whichever is more convenient right now.
- **Sovereignty is non-negotiable.** No feature may assume internet access is available;
  see `architecture/17_air_gapped_architecture.md`.
- **Every action is attributable.** No feature may act without an audit trail; see
  `features/17_audit/`.
- **Scope is explicit.** If it's not described in `features/` or `02_SCOPE_AND_NON_GOALS.md`
  as in-scope, it isn't in-scope — see `later/` for the deferred list.

See `18_DOCUMENTATION_INDEX.md` for a flat, alphabetized index of every file in this tree.
