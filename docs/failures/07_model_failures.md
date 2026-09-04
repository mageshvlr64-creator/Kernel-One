# Model Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The selected model produces a malformed response, crashes, or returns an unexpected format.

## Detection

Response schema validation in the Inference Gateway (features/03_inference_gateway/).

## System response

Treated as `MODEL_UNAVAILABLE` if the runtime itself failed, or a retried request if the response was merely malformed once (runtime/11_retry_policy.md, model-inference class).

## Error code

`MODEL_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Router retries once, then falls back per features/02_model_router/09_fallback_routing.md.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
