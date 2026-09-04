# API Overview

> Canonical entry point for the API surface. Individual endpoint files (`02_authentication_api.md`
> through `25_metrics_api.md`) are the source of truth for their own routes; this file defines
> the conventions all of them share and the full route index.

## Version

All application endpoints are under `/api/v1/`. `/healthz`, `/readyz`, and `/metrics` are
unversioned infrastructure endpoints (no auth, no envelope — see `24_health_api.md`,
`25_metrics_api.md`).

## Authentication and authorization

Bearer token issued by `POST /api/v1/auth/login` (`02_authentication_api.md`). Every
state-changing and classification-sensitive read passes through the policy engine
(`features/21_policy_engine/`) before executing (REQ-SEC-001) — see
`reference/05_permission_matrix.md` for the role table.

## Envelope, pagination, errors

Defined once in `docs/schemas/02_api_schema.md`. Every endpoint below uses that envelope; no
endpoint file redefines it.

## Route index

| Category | File |
|---|---|
| Authentication | `02_authentication_api.md` |
| Users | `03_users_api.md` |
| Workspaces | `04_workspaces_api.md` |
| Chat / Conversations | `05_chat_api.md` |
| Tasks | `06_tasks_api.md` |
| Execution | `07_execution_api.md` |
| Models | `08_models_api.md` |
| Model Registry | `09_model_registry_api.md` |
| Model Router | `10_model_router_api.md` |
| Documents | `11_documents_api.md` |
| Knowledge / Indexing | `12_knowledge_api.md` |
| Search / RAG | `13_search_api.md` |
| Evidence | `14_evidence_api.md` |
| Tools | `15_tools_api.md` |
| Sandbox | `16_sandbox_api.md` |
| Artifacts | `17_artifacts_api.md` |
| Approvals | `18_approval_api.md` |
| Audit | `19_audit_api.md` |
| Policy | `20_policy_api.md` |
| RBAC | `21_rbac_api.md` |
| Network Sovereignty | `22_network_api.md` |
| Admin | `23_admin_api.md` |
| Health | `24_health_api.md` |
| Metrics | `25_metrics_api.md` |
| Error contracts | `26_error_contracts.md` |

## Idempotency

State-changing endpoints marked idempotent in `docs/runtime/15_idempotency.md` accept an
`Idempotency-Key` header; a retried request with the same key returns the original result
rather than re-executing.

## Rate limits

See `docs/schemas/02_api_schema.md` — 60 req/min per user for `interactive-*` operation
classes (CONFIG DEFAULT), returning `429 RATE_LIMITED`.
