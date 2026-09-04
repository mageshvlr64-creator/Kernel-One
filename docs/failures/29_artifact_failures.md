# Artifact Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Artifact generation fails at any stage not covered by the format-specific files below.

## Detection

Artifact Engine's validation stage (features/15_artifact_engine/13_artifact_failures.md).

## System response

Artifact state → `FAILED`.

## Error code

`TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried once per artifact-generation operation class; user notified if it fails again.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
