# Failure Matrix (Reference)

> Restates `failures/`'s 44 entries as a flat lookup by owning component, for quickly finding
> "what can go wrong with X."

| Component | Relevant failure files |
|---|---|
| Model/Inference | `07_model_failures.md`, `08_model_timeout.md`, `09_model_oom.md`, `10_model_unavailable.md`, `11_model_corruption.md`, `23_vlm_failures.md`, `24_embedding_failures.md` |
| Router | `12_router_failures.md` |
| Agent Kernel | `13_agent_failures.md`, `14_planning_failures.md` |
| Tools | `15_tool_failures.md`, `16_tool_timeout.md`, `17_tool_permission_denied.md`, `18_filesystem_failures.md` |
| Database | `19_database_failures.md` |
| Documents/OCR | `20_document_failures.md`, `21_pdf_failures.md`, `22_ocr_failures.md` |
| Retrieval | `25_retrieval_failures.md`, `26_reranker_failures.md` |
| Evidence/Citations | `27_citation_failures.md`, `28_evidence_failures.md` |
| Artifacts | `29_artifact_failures.md` through `33_pdf_generation_failures.md` |
| Sandbox/Containers | `34_sandbox_failures.md`, `35_container_failures.md` |
| Network/Storage/Queue | `36_network_failures.md`, `37_storage_failures.md`, `38_queue_failures.md` |
| Observability/Audit | `39_observability_failures.md`, `40_audit_failures.md` |
| Approvals | `41_approval_failures.md` |
| Backup/Recovery | `42_backup_failures.md`, `43_recovery_failures.md`, `44_partial_failure_recovery.md` |
| Auth/Access | `05_authentication_failures.md`, `06_authorization_failures.md` |
| Input/Config | `03_user_errors.md`, `04_configuration_errors.md` |

## Full detail

See the individual failure files for trigger/detection/response/recovery — this table is a
routing index only.
