# Restore Operations

> Concrete restore procedure, used both for verification (`08_backup_operations.md`) and for
> actual disaster recovery (`13_disaster_recovery.md`).

## Procedure

1. Stop all application services (`03_shutdown.md`) — a restore against a live database risks
   inconsistent state.
2. Restore the PostgreSQL dump/WAL archive to the target point in time.
3. Restore the object storage snapshot to the same or a later point in time than the database
   restore (object storage may lag slightly behind the database without harm, since a
   `storage_uri` referencing a not-yet-restored object simply fails a subsequent read with
   `DEPENDENCY_UNAVAILABLE` rather than corrupting anything).
4. Verify the `audit_events` hash chain validates end-to-end on the restored database
   (REQ-SEC-005) before resuming service.
5. Run `02_startup.md`.
6. Spot-check: log in as a known test user, open a known Task, confirm its Evidence/Artifact
   links still resolve.

## Point-in-time restore

If WAL archiving is configured, restore to any point within the retention window, not only to
the nightly snapshot boundary — required for incident scenarios where the exact moment of
corruption/compromise is known (`10_incident_response.md`).

## Post-restore audit entry

Every restore operation is itself logged as an operational event (not an `AuditEvent` in the
application sense, since the application wasn't running — logged in `05_log_management.md`'s
infrastructure log instead) with: who performed it, why, source backup timestamp, and
verification result.
