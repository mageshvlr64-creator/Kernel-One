# Storage Operations

> Concrete procedures for the two storage systems: PostgreSQL (relational + vector) and
> object storage (MinIO/S3-compatible, DEC-003).

## Capacity monitoring

- Alert at 80% disk utilization on the PostgreSQL volume; hard-stop new writes (return
  `DEPENDENCY_UNAVAILABLE`, never silently corrupt) at 95%.
- Object storage: alert at 80% of the configured bucket quota; document uploads return
  `INVALID_REQUEST` with a specific "storage full" reason rather than a generic failure once
  the quota is reached.

## Routine maintenance

1. Weekly `VACUUM ANALYZE` on `document_chunks`, `audit_events`, `tool_invocations` (highest
   write-volume tables).
2. Monthly review of the `pgvector` HNSW index size vs. corpus growth; reindex if query
   latency in `features/13_knowledge_fabric/` degrades beyond its performance budget
   (`runtime/11_retry_policy.md` operation class `interactive-read`).
3. Object storage: verify lifecycle policy correctly transitions soft-deleted Document/Artifact
   blobs to a "pending purge" state after the 30-day retention window (`domain/02_workspace_model.md`
   soft-delete note), then confirm actual deletion after the purge job runs.

## Adding storage capacity

Expanding the PostgreSQL volume or object storage bucket is a deployment-level change
(`deployment/`), not an application config change — no `16_ENVIRONMENT_AND_CONFIGURATION.md`
key controls storage size directly.
