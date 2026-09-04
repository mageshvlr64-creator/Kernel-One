# Document Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Any failure during the Document state machine's UPLOADED→READY progression not covered by the more specific files below.

## Detection

Document Ingestion's per-stage error handling (features/10_document_ingestion/13_ingestion_failures.md).

## System response

Document state → `FAILED` with a reason; never left stuck in an intermediate state.

## Error code

`INVALID_REQUEST / DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User re-uploads; if the failure was transient (dependency unavailable), a retry of the same file may succeed.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
