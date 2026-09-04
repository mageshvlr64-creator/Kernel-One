# PPTX Generation Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Same class of failure, specific to presentation generation.

## Detection

Same validation pattern.

## System response

Artifact state → `FAILED`.

## Error code

`TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Same as DOCX.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
