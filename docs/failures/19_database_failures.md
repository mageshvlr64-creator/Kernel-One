# Database Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Query timeout, connection pool exhaustion, constraint violation.

## Detection

Database client's error handling in each service.

## System response

`DEPENDENCY_UNAVAILABLE` (connection issues), `RESOURCE_CONFLICT` (constraint violation, e.g. duplicate approval decision).

## Error code

`DEPENDENCY_UNAVAILABLE / RESOURCE_CONFLICT` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried per `interactive-read`/`interactive-write` operation class rules (runtime/11_retry_policy.md); sustained failure pages the operator.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
