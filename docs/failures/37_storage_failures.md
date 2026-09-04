# Storage Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Object storage (MinIO) is unreachable, or a specific object is missing/corrupted.

## Detection

Storage client error handling; checksum verification on read (domain/06_document_model.md `sha256` field checked against the retrieved object).

## System response

`DEPENDENCY_UNAVAILABLE` (unreachable) or a distinct 'file corrupted' error if the checksum fails on a retrieved object.

## Error code

`DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried per interactive-read operation class; a checksum mismatch triggers restoration from backup (operations/09_restore_operations.md) for that specific object.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
