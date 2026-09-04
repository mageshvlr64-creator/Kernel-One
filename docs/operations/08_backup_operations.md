# Backup Operations

> Concrete backup procedure. See `26_backup_recovery` feature group for the system's own
> backup-triggering behavior; this file is the operator-facing runbook for verifying and
> managing those backups.

## What is backed up

| Component | Method | Frequency | Retention |
|---|---|---|---|
| PostgreSQL (all tables incl. `audit_events`) | `pg_dump` (or WAL archiving for point-in-time recovery, if configured) | Nightly full + continuous WAL archiving | 30 days (CONFIG DEFAULT) |
| Object storage (Documents, Artifacts) | Bucket replication/snapshot to a separate on-prem volume — never a cloud target (REQ-NET-001) | Nightly | 30 days |
| Model registry configuration | Included in PostgreSQL dump (the `models` table) | Nightly | 30 days |
| Policy configuration | Included in PostgreSQL dump (the `policies` table) | Nightly | 30 days |

## Verification procedure (required, not optional)

1. After each nightly backup, run an automated restore into a scratch/staging database.
2. Verify row counts on `tasks`, `documents`, `audit_events` match the source within an
   acceptable delta (accounting for activity during the backup window).
3. Verify the `audit_events` hash chain still validates in the restored copy (REQ-SEC-005) —
   a backup that fails hash-chain verification is flagged as **corrupt**, not silently kept as
   the latest good backup.
4. Alert the operator if verification fails; do not silently retain a backup that failed
   verification as if it were valid.

## Target completion time

Full backup of a 50GB deployment completes within 30 minutes (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
background-job operation class) — **CONFIG DEFAULT**, not yet benchmarked against a production
corpus (tracked alongside DEC-014).
