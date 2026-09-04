# Router Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

No model satisfies the requested capability + classification + hardware-fit combination.

## Detection

Router's selection logic (features/02_model_router/) returns no candidate.

## System response

`MODEL_NOT_APPROVED` if a classification mismatch is the cause, `MODEL_UNAVAILABLE` if no healthy model exists for the capability at all.

## Error code

`MODEL_NOT_APPROVED / MODEL_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator registers an appropriate model or adjusts the requested classification/capability.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
