# Navigation

> Canonical route map. Screen files above define what each route shows; this file defines how
> a user gets there.

## Top-level navigation (persistent sidebar)

| Label | Route | Screen file | Visible to |
|---|---|---|---|
| Workbench | `/` | `05_workbench_screen.md` | all roles |
| Chat | `/chat/:conversationId?` | `06_chat_interface.md` | all roles |
| Documents | `/documents` | `15_knowledge_browser.md` | all roles with `Document:read` |
| Assets | `/assets` | `23_asset_view.md` | all roles with `Equipment:read` |
| Workflows | `/workflows` | industrial workflow launch points, `workflows/*.md` (inspection intelligence, document comparison, engineering calculation) | all roles with the relevant `Document:read`/`Tool:execute` permission |
| Reports | `/reports` | generated Artifact list, filtered to report-type Artifacts (`workflows/07_report_generation.md`, `features/15_artifact_engine/`) | all roles with `Artifact:read` |
| Approvals | `/approvals` | `11_approval_ui.md` | Administrator, SecurityOfficer only |
| Security | `/security` | `12_security_panel.md` | Administrator, SecurityOfficer only |
| Network | `/network` | `13_network_panel.md` | all roles |
| Models | `/models` | `14_model_panel.md` | all roles (detail limited by role) |
| Admin | `/admin` | `16_admin_console_ui.md` | Administrator, Operator (subset) |

## Task-scoped navigation (breadcrumb from a Task)

`/tasks/:taskId` (`07_task_interface.md`) → `/tasks/:taskId/graph` (`08_execution_graph_ui.md`)
→ `/tasks/:taskId/evidence` (`09_evidence_panel.md`) → `/tasks/:taskId/artifacts`
(`10_artifact_panel.md`).

## Guard behavior

A route whose screen requires a role/permission the current user lacks renders
`20_permission_denied_states.md`'s 403 page instead of the target screen — the route itself
still resolves (no dead link), but the content is replaced.

## Deep-linking

Every route above is directly linkable/bookmarkable and re-derives its state from the API on
load — no client-only state required to render a valid deep link correctly.
