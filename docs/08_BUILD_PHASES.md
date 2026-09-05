# Build Phases

> Canonical, executable roadmap. Each phase has an objective, exact deliverables, dependencies
> (see `10_DEPENDENCY_GRAPH.md`), tests, and exit criteria. A phase is not "done" until its
> exit criteria pass — moving on with a failing exit criterion is a documented risk, not a
> silent skip.

| Phase | Objective | Deliverables | Depends on | Exit criteria |
|---|---|---|---|---|
| **0 — Foundation** | Repo/spec/tooling in place | This `docs/` tree; repo skeleton per `15_CODEBASE_TARGET_STRUCTURE.md`; CI pipeline running lint + empty test suite | — | CI green on an empty commit; `docs/` spec-lint (`58_SPECIFICATION_LINTING` procedure — see `18_DOCUMENTATION_INDEX.md`) passes |
| **1 — Core backend** | Database, config, auth | `schemas/01_database_schema.md` DDL applied via migration; `19_identity_and_rbac` (login/session); `16_ENVIRONMENT_AND_CONFIGURATION.md` config loader | Phase 0 | `POST /api/v1/auth/login` works against a seeded Administrator user; `TEST-AUTH-001` passes |
| **2 — Model runtime + inference gateway** | At least one local model reachable through the gateway | `01_model_management`, `03_inference_gateway` (one provider, e.g. llama.cpp), `02_model_router` with single-capability routing | Phase 1 | A raw inference call through the gateway returns a completion; `TEST-ROUTER-001` passes |
| **3 — Agent kernel + tool gateway** | Agent can plan and execute a trivial tool call | `04_agent_kernel` (plan/execute loop, no replanning yet), `05_tool_gateway`, `07_calculator_tool` (simplest tool) | Phase 2 | End-to-end: a task asking a math question produces a correct, tool-verified answer; `TEST-E2E-000` (smoke) passes |
| **4 — Filesystem + sandbox** | Agent can read files and run code safely | `06_filesystem_tool`, `09_code_execution` | Phase 3 | `SEC-TEST-003`, `SEC-TEST-005` pass |
| **5 — Documents/OCR/RAG** | Agent can answer from an uploaded document | `10_document_ingestion`, `11_ocr`, `13_knowledge_fabric` | Phase 4 | `TEST-OCR-001`, `TEST-RAG-003` pass |
| **6 — Evidence/provenance** | Every claim in an answer is citation-backed | `14_evidence_and_provenance` | Phase 5 | `TEST-EVIDENCE-001` passes |
| **6.5 — Industrial Intelligence** | Asset entities, knowledge graph, revision comparison, and conflict detection are real and queryable, not just document-type workflows | `domain/20_asset_model.md` schema applied; `industrial/13_asset_knowledge_graph.md` relationships (`governed_by` join table, entity resolution); `industrial/05-06` revision comparison; `industrial/14_knowledge_conflict_detection.md`; `ui/23_asset_view.md` | Phase 6 | `TEST-REVISION-001` passes; a seeded Equipment row with two conflicting governing Documents produces a `CONFLICT DETECTED` result, not a silently-picked answer |
| **7 — Artifacts + approvals** | Agent produces a real DOCX with a human approval gate | `15_artifact_engine`, `16_human_approval` | Phase 6.5 | `TEST-APPROVAL-001` passes; generated `.docx` opens correctly in a real Office viewer, including the 11-section report structure (`workflows/07_report_generation.md`) |
| **8 — RBAC/security/audit hardening** | Full six-role matrix enforced, complete audit trail | `20_data_classification`, `21_policy_engine` fully wired; `17_audit` hash-chain; `18_network_sovereignty` monitor | Phase 7 | All `SEC-TEST-###` pass; `TEST-AUDIT-001`, `TEST-AUDIT-002` pass |
| **9 — Observability/deployment** | Deployable, observable on PROFILE-B | `25_observability`, `deployment/03_docker_compose.md` profile for PROFILE-B, `24_health_api` | Phase 8 | `readyz`/`healthz` correct under induced dependency failure; metrics visible in Grafana |
| **10 — End-to-end demo + hardening** | Full reproducible demo, benchmarked numbers | `demo/01_demo_overview.md` scenario passes live; DEC-013/DEC-014 resolved (model pinned, perf validated) | Phase 9 | Full demo runbook completes under 5 minutes on PROFILE-B, three times in a row, with sovereignty panel green throughout |

## Rule

Not every feature group needs to be "enterprise complete" before the demo — Phase 10's exit
criterion is the demo script, not 100% of every feature file's acceptance criteria. Anything
not required for the demo but still V1-scoped is finished after Phase 10, tracked explicitly
rather than silently declared done.
