# Storage Boundaries

> Which component may read/write which storage system directly.

## Boundaries

| Storage | Direct write access | Direct read access |
|---|---|---|
| PostgreSQL tables (per `05_component_boundaries.md` ownership) | Only the owning service | Any service, through the owner's query interface — but classification/workspace filters (`features/20_data_classification/`) apply to every read, not only the owner's own reads |
| Object storage (Documents, Artifacts) | Document Ingestion, Artifact Engine respectively | Any service holding a valid `storage_uri` AND passing the classification check for that document/artifact |
| Task workspace filesystem (sandboxed, per-task) | Filesystem Tool, Code Execution (within that task's workspace only) | Same, workspace-scoped |
| Audit event store | Audit Service only (append) | Any service via the Audit API, filtered by role (`api/19_audit_api.md`) |

## Rule

"Direct" access above means at the database/filesystem-driver level — every other form of
access goes through an API/internal-interface call, which is where the classification and
permission checks actually live (this file names the boundary; `features/20_data_classification/`
and `features/21_policy_engine/` define the check itself).
