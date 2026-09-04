# Recovery Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A restore operation itself fails (e.g. the backup was corrupt) or produces a database that fails hash-chain verification.

## Detection

Restore verification step (operations/09_restore_operations.md step 4).

## System response

Restore is not considered complete/successful; operator falls back to an earlier backup and re-attempts, per `13_disaster_recovery.md`'s scenario table.

## Error code

`N/A (operational procedure, not an API error)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

This is exactly why `08_backup_operations.md` requires an automated restore-verification test on every nightly backup — catching this at backup time, not only at actual-disaster time, is the whole point of that verification step.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
