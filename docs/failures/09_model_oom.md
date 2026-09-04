# Model Out-of-Memory

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A request's context length or batch size exceeds available VRAM for the selected model.

## Detection

Runtime-reported OOM error, or a pre-flight context-length check against `Model.context_window` (schemas/06_model_schema.md).

## System response

`MODEL_RESOURCE_EXHAUSTED` (503).

## Error code

`MODEL_RESOURCE_EXHAUSTED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Router falls back to a smaller/cpu-fallback capability slot if configured (07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md); otherwise surfaced to the user.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
