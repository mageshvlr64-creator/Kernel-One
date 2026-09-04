# User Errors

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Malformed request, invalid field value, missing required field.

## Detection

Schema validation at the API layer (schemas/02_api_schema.md) before any business logic runs.

## System response

`INVALID_REQUEST` with field-level `details`.

## Error code

`INVALID_REQUEST` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User corrects the field and resubmits; no server-side state was touched.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
