# Storage Budgets

> Disk/object storage growth assumptions, for capacity planning
> (`operations/07_storage_operations.md`).

## Growth assumptions (CONFIG DEFAULT, not benchmarked against real usage patterns)

| Data type | Approx. size per unit | Notes |
|---|---|---|
| Document (average) | 2-10MB per document (scanned PDFs are larger than native text) | Object storage |
| DocumentChunk embeddings | ~3KB per chunk (768-dim float32 vector + metadata) | PostgreSQL |
| AuditEvent | ~1KB per event | PostgreSQL, indefinite retention (REQ-SEC-005) — this is the fastest-growing table over time and the one most worth monitoring |
| Artifact | 100KB-5MB depending on type/length | Object storage |

## Retention-driven growth control

Document/Artifact soft-deletes purge after 30 days (CONFIG DEFAULT,
`domain/02_workspace_model.md`); AuditEvent never purges — operators must plan storage growth
assuming the audit table grows unboundedly for the life of the deployment, and size
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s storage column accordingly for their expected
usage volume and retention horizon.
