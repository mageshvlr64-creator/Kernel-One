# Backup Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A scheduled backup job fails partway (e.g. disk full on the backup target, or the database dump process crashes).

## Detection

Backup job's own exit-code and completeness check (operations/08_backup_operations.md verification procedure).

## System response

Backup marked failed/incomplete, never silently retained as if it were a valid backup; alert fires immediately (not waiting for the next scheduled backup) since backup gaps compound risk.

## Error code

`N/A (operational alert, not an API error)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator investigates and re-runs; if repeated, treat as approaching `13_disaster_recovery.md` territory — don't let more than one backup cycle pass unaddressed.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
