# Traceability Matrix

> Requirement → Design → Component → API/Schema → Test → Acceptance criterion. No requirement
> in `03_REQUIREMENTS.md` exists without a row here; no row here references a nonexistent file.

| Requirement | Design doc | Component | API/Schema | Test | Acceptance criterion |
|---|---|---|---|---|---|
| REQ-NET-001 | `architecture/17_air_gapped_architecture.md` | `features/18_network_sovereignty/` | `schemas/17_network_event_schema.md`, `api/22_network_api.md` | `TEST-NET-001` | Zero external connections during full demo |
| REQ-NET-002 | `architecture/18_restricted_network_architecture.md` | `features/18_network_sovereignty/02_network_modes.md` | `16_ENVIRONMENT_AND_CONFIGURATION.md#NETWORK_MODE` | `TEST-NET-003` | Mode switch changes behavior with no code change |
| REQ-NET-003 | `ui/13_network_panel.md` | `features/18_network_sovereignty/12_sovereignty_status.md` | `api/22_network_api.md` | `TEST-NET-001` | Panel visible/updating throughout demo |
| REQ-SEC-001 | `security/01_security_architecture.md` | `features/19_identity_and_rbac/`, `features/21_policy_engine/` | `schemas/14_permission_schema.md`, `api/21_rbac_api.md` | `SEC-TEST-002`, `SEC-TEST-007` | Every state-changing call authorization-checked |
| REQ-SEC-002 | `security/08_sandbox_escape.md` | `features/09_code_execution/` | `api/16_sandbox_api.md` | `SEC-TEST-003` | Generated code cannot reach the network |
| REQ-SEC-003 | `security/05_prompt_injection.md` | `features/04_agent_kernel/09_observation_handling.md` | — | `SEC-TEST-004` | Embedded document instructions don't trigger tool calls |
| REQ-SEC-004 | `security/09_path_traversal.md` | `features/06_filesystem_tool/05_path_validation.md` | `api/15_tools_api.md` | `SEC-TEST-005` | Path traversal attempts rejected before I/O |
| REQ-SEC-005 | `security/16_audit_tampering.md` | `features/17_audit/10_audit_integrity.md` | `schemas/15_audit_event_schema.md` | `TEST-AUDIT-002` | Application DB role cannot UPDATE/DELETE audit rows |
| REQ-FUNC-001 | `workflows/05_document_qa.md` | `features/10_document_ingestion/`, `13_knowledge_fabric/`, `14_evidence_and_provenance/` | `api/11_documents_api.md`, `13_search_api.md`, `14_evidence_api.md` | `TEST-E2E-001` | Every claim in the demo answer has a valid citation |
| REQ-FUNC-002 | `features/04_agent_kernel/01_agent_kernel_overview.md` | `features/04_agent_kernel/` | `api/06_tasks_api.md`, `07_execution_api.md` | `TEST-E2E-002` | Coding demo completes without manual intervention beyond approvals |
| REQ-FUNC-003 | `features/16_human_approval/01_approval_system.md` | `features/16_human_approval/` | `api/18_approval_api.md` | `TEST-APPROVAL-001` | High-risk step blocked pending `decision=approved` |
| REQ-FUNC-004 | `features/13_knowledge_fabric/12_permission_filtering.md` | `features/13_knowledge_fabric/` | `api/13_search_api.md` | `SEC-TEST-001`, `TEST-RAG-003` | Unauthorized retrieval returns zero restricted-doc results |
| REQ-FUNC-005 | `features/14_evidence_and_provenance/09_unsupported_claim_detection.md` | `features/14_evidence_and_provenance/` | `schemas/09_evidence_schema.md` | `TEST-EVIDENCE-001` | Sampled citations resolve to real matching passages |
| REQ-AI-001 | `features/02_model_router/01_router_overview.md` | `features/02_model_router/` | `api/10_model_router_api.md` | `TEST-ROUTER-004` | Model swap via config only, no code change |
| REQ-AI-002 | `features/11_ocr/01_ocr_overview.md` | `features/11_ocr/` | `api/12_knowledge_api.md` | `TEST-OCR-001` | Reference scanned page fully indexed |
| REQ-AI-003 | `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` | `features/01_model_management/`, `02_model_router/05_resource_fit.md` | `schemas/06_model_schema.md` | `TEST-ROUTER-005` | Router rejects by total_parameters, not active_parameters |
| REQ-PERF-001 | `performance/01_performance_requirements.md` | cross-cutting | — | `TEST-PERF-001` | Demo completes < 5 min on PROFILE-B (DESIGN LIMIT, DEC-014 pending) |
| REQ-DATA-001 | `features/20_data_classification/08_classification_inheritance.md` | `features/20_data_classification/` | `schemas/07_document_schema.md`, `11_artifact_schema.md` | `TEST-CLASS-001` | Artifact inherits max classification of cited evidence |
| REQ-AUD-001 | `features/17_audit/01_audit_system.md` | `features/17_audit/` | `schemas/15_audit_event_schema.md` | `TEST-AUDIT-001` | Mutation count == audit event count for a scripted sequence |

## Coverage rule

Every row's Component and API/Schema columns must point to files that exist (verified by the
reference audit in this repository's generation process); every Test ID must also appear in
`testing/21_security_testing.md` or be a named `TEST-*` referenced from the owning feature's
"Test requirements" section.
