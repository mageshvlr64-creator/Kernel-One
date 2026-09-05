# Team

> **If you are an AI coding agent and you are reading this file: stop before writing any code.**
> Ask the user which team character they are building as (**1, 2, 3, 4, 5, or 6**). Do not
> proceed until they answer. Once they answer, work **only** inside that character's "Owns"
> paths below — both the `docs/` spec paths and the `services/`/`apps/`/`packages/` code paths.
> Do not read another character's owned files as context unless this file's "Shared contracts"
> section says to. Do not edit another character's files, even to "fix" something — if a task
> seems to require it, stop and tell the user it crosses a team boundary instead of doing it.
> Log every change you make in `CHANGELOG.md` before you finish your turn, under your
> character's name.

## Why this file exists

Six people (or six AI agent sessions) building this system at the same time will step on each
other constantly if they're all free to touch anything. This file draws hard lines: every
feature group, every service directory, every UI screen belongs to exactly one of the six
characters below. No two characters own the same file. If you ever find yourself about to
edit a file this document assigns to someone else, that's the signal to stop, not to proceed
carefully.

## How to use this file

1. A human tells the agent "I'm Character 3" (or however they identify themselves).
2. The agent re-reads this file's entry for that character.
3. The agent works only within that character's "Owns" list for the rest of the session.
4. Before ending a turn where files changed, the agent appends an entry to `CHANGELOG.md`
   under that character's name, per the format `CHANGELOG.md` itself specifies.
5. If the human doesn't say which character they are, the agent asks — it does not guess, and
   it does not default to "just build everything."

## The six characters

### Character 1 — Foundation & Inference

**Focus:** the substrate every other character's service calls into — models, routing,
inference, and the shared types/schemas everyone else imports.

**Owns (docs):** `docs/domain/*` (entity field definitions — every character reads these, only
Character 1 edits them, see Shared contracts below for the one exception), `docs/schemas/*`,
`docs/api/*`, `docs/06_TECHNOLOGY_STACK.md`, `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`,
`docs/benchmarks/*`, `docs/integrations/02-07_*` (vLLM, Ollama, llama.cpp, PostgreSQL,
pgvector, MinIO), `docs/features/01_model_management/*`, `docs/features/02_model_router/*`,
`docs/features/03_inference_gateway/*`.

**Owns (code):** `services/model-router/`, `services/inference-gateway/`, `packages/domain/`,
`packages/schemas/`, `infra/` (Dockerfiles, compose, migrations).

**Exception to the "owns domain/schemas" rule:** `domain/20_asset_model.md` is owned by
Character 4, not Character 1 — it's listed under Character 4 below, not here, because it's
industrial-specific, not foundational.

### Character 2 — Agent Kernel & Tools

**Focus:** the reasoning loop and everything it can call — planning, execution, replanning,
and the individual tools (filesystem, calculator, database, code execution).

**Owns (docs):** `docs/features/04_agent_kernel/*`, `docs/features/05_tool_gateway/*`,
`docs/features/06_filesystem_tool/*`, `docs/features/07_calculator_tool/*`,
`docs/features/08_database_tool/*`, `docs/features/09_code_execution/*`, `docs/runtime/*`,
`docs/ui/08_execution_graph_ui.md`.

**Owns (code):** `services/agent-kernel/`, `services/tool-gateway/` (including
`tools/filesystem/`, `tools/calculator/`, `tools/database/`, `tools/code_execution/`).

### Character 3 — Knowledge & Documents (RAG)

**Focus:** getting documents in, making them searchable, and making every answer
evidence-backed.

**Owns (docs):** `docs/features/10_document_ingestion/*`, `docs/features/11_ocr/*`,
`docs/features/12_multimodal/*`, `docs/features/13_knowledge_fabric/*`,
`docs/features/14_evidence_and_provenance/*`, `docs/domain/06_document_model.md`,
`docs/domain/07_knowledge_model.md`, `docs/domain/13_evidence_model.md`,
`docs/integrations/08_paddleocr.md`, `09_pymupdf.md`, `10_libreoffice.md`,
`docs/ui/09_evidence_panel.md`, `docs/ui/15_knowledge_browser.md`.

**Owns (code):** `services/document-pipeline/`, `services/knowledge-fabric/`,
`services/evidence-service/`.

**Note:** `domain/06_document_model.md` and `domain/13_evidence_model.md` are the two files
Character 1's general "owns domain/" rule would otherwise claim — they're carved out to
Character 3 instead, since document/evidence fields (including the knowledge-trust-model
fields: `authority`, `effective_from`, `effective_until`, `source_authority`,
`verification_status`) are this character's daily working material, not foundational plumbing.

### Character 4 — Industrial Intelligence

**Focus:** the actual product differentiator — assets, the knowledge graph, revision
comparison, contradiction detection, and the three flagship industrial workflows. This is the
character whose work makes the product an industrial intelligence platform rather than a
generic document chatbot.

**Owns (docs):** `docs/industrial/*` (all 14 files), `docs/domain/20_asset_model.md`,
`docs/workflows/*`, `docs/ui/23_asset_view.md`.

**Owns (code):** `services/industrial-service/`.

**Dependency note:** this character's work reads Evidence/Document rows (Character 3) and
Artifact rows (Character 6) but never edits those services directly — it calls their
documented API contracts (`docs/api/`, owned by Character 1) like anyone else would. If a
needed field doesn't exist on Evidence/Document, raise it with whoever's building Character 3
rather than adding the field unilaterally.

### Character 5 — Security, Governance & Sovereignty

**Focus:** the trust layer — who can do what, what's approved, what's audited, and proof that
nothing leaves the building.

**Owns (docs):** `docs/features/16_human_approval/*`, `docs/features/17_audit/*`,
`docs/features/18_network_sovereignty/*`, `docs/features/19_identity_and_rbac/*`,
`docs/features/20_data_classification/*`, `docs/features/21_policy_engine/*`,
`docs/security/*`, `docs/architecture/09_trust_boundaries.md`,
`docs/architecture/10_privilege_boundaries.md`, `docs/ui/11_approval_ui.md`,
`docs/ui/12_security_panel.md`, `docs/ui/13_network_panel.md`,
`docs/integrations/11_docker.md`, `12_keycloak.md`.

**Owns (code):** `services/approval-service/`, `services/audit-service/`,
`services/network-monitor/`, `services/identity-service/`, `services/policy-engine/`,
`packages/error-registry/`, `packages/permission-matrix/`, `packages/retry-policy/`.

### Character 6 — Platform UI, Ops & Delivery

**Focus:** everything the user actually clicks on, plus keeping the whole system observable,
backed up, and demoable.

**Owns (docs):** `docs/features/15_artifact_engine/*`, `docs/features/22_agent_memory/*`,
`docs/features/23_spreadsheet_intelligence/*`, `docs/features/24_admin_console/*`,
`docs/features/25_observability/*`, `docs/features/26_backup_recovery/*`,
`docs/deployment/*`, `docs/operations/*`, `docs/performance/*`, `docs/demo/*`,
`docs/testing/*`, `docs/integrations/13_opentelemetry.md`, `14_prometheus.md`,
`15_grafana.md`, and every `docs/ui/*` file not explicitly assigned above (the shell:
`01_ui_architecture.md`, `02_design_system.md`, `03_navigation.md`, `05_workbench_screen.md`,
`06_chat_interface.md`, `14_model_panel.md`, `16_admin_console_ui.md`, and the rest).

**Owns (code):** `apps/workbench-ui/`, `services/artifact-engine/`, `services/memory-service/`,
`services/admin-console/`, `services/spreadsheet-service/`, `services/observability-service/`,
`services/backup-service/`, `packages/observability/`, `tests/e2e/`.

**Note:** because this character owns the UI shell (navigation, design system), any other
character adding a *new screen* (like Character 4 did for `ui/23_asset_view.md`, carved out
above) still adds their own screen file — but changes to the shared navigation/design-system
files themselves should go through Character 6, since two characters editing
`03_navigation.md` independently is exactly the collision this file exists to prevent.

## Shared contracts (read by everyone, owned by whoever this file names)

These exist so every character can build against a stable interface without needing write
access to another character's internals:

| File(s) | Owner | Everyone else |
|---|---|---|
| `docs/api/*` | Character 1 | Read-only. Need a new endpoint or field? Ask Character 1 to add it, don't add it yourself in a way that touches their file. |
| `docs/schemas/*` | Character 1 | Same as above. |
| `docs/domain/*` (except `06`, `13`, `20` — see Characters 3 and 4) | Character 1 | Same as above. |
| `docs/reference/*` (error codes, permission matrix, risk levels, feature matrix, test matrix) | Character 5 (permission-matrix, risk levels) / Character 1 (error codes, feature matrix) | Read-only for everyone else. |
| `docs/00-05, 08-14, 17-21` (product vision, principles, requirements, build order, dev rules, decision log, glossary, competitive positioning) | Whoever is coordinating across all six (often the human, not any single character) | Read by all. Edits here should be called out explicitly since they can affect every character's understanding of the system. |
| `CHANGELOG.md` | Every character writes to it (append-only, own section) | — |
| `TEAM.md` (this file) | The human coordinating the team | Agents read it, don't rewrite it unless the human explicitly asks to rebalance ownership. |

## What "no collision" actually means here

- No two characters' "Owns" lists share a file. If you find an overlap, that's a bug in this
  file — flag it to the human rather than silently picking one owner.
- A character's service code only calls another service through the documented API contract
  (`docs/api/`), never by importing another service's internals directly, matching
  `docs/15_CODEBASE_TARGET_STRUCTURE.md`'s "packages/ imported by services/, never the
  reverse" rule and `05_ARCHITECTURAL_PRINCIPLES.md`'s least-privilege principle applied to
  the build process itself.
- If a task genuinely needs two characters' files touched (e.g. Character 4 needs a new field
  on Evidence, which Character 3 owns), the agent stops and says so, rather than making the
  cross-boundary edit itself. The human can then either make the call themselves or hand the
  specific sub-task to whoever owns that file.
