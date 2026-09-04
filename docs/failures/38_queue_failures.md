# Queue Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A background job queue (backups, reindexing) is unavailable or a job fails.

## Detection

Queue worker's error handling (runtime/17_queueing.md).

## System response

Job marked failed, retried per `background-job` operation class (runtime/11_retry_policy.md).

## Error code

`DEPENDENCY_UNAVAILABLE / INTERNAL_ERROR` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator investigates if a job fails after its single retry; V1's queueing is in-process (no separate broker), so a queue failure is typically a symptom of a broader service failure, not an independent failure mode.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
