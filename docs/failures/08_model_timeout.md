# Model Timeout

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Inference call exceeds the `model-inference` operation class timeout (30s text / 60s vision, runtime/11_retry_policy.md).

## Detection

Gateway-side timeout timer per request.

## System response

`INFERENCE_TIMEOUT` (504); in-flight generation is cancelled server-side, not left running.

## Error code

`INFERENCE_TIMEOUT` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

One retry per policy, then surfaced to the user with a clear 'took too long' message (reference/01_error_codes.md).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
