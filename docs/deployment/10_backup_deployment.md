# Backup Infrastructure Deployment

> Deploying the backup mechanism itself (distinct from `operations/08_backup_operations.md`'s
> day-to-day procedure).

## Components

- A backup target volume/host, physically or logically separate from the primary
  Database/Object Storage volumes (a backup on the same disk as the primary data protects
  against nothing).
- A scheduled job runner (cron, or the orchestrator's native scheduling) triggering
  `pg_dump`/WAL archiving and object storage replication per `operations/08_backup_operations.md`'s
  schedule.
- The restore-verification scratch environment (`operations/08_backup_operations.md`
  verification procedure) — this should be provisioned as part of initial deployment, not
  added later, so verification is exercised from the very first backup.

## Sovereignty constraint

The backup target must itself be within the deployment's permitted network boundary — a cloud
backup target is categorically excluded for `air_gapped`/`restricted`/`on_premise`
deployments, same as any other external service (REQ-NET-001/002).
