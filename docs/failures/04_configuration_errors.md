# Configuration Errors

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A required environment variable is missing or invalid at startup (16_ENVIRONMENT_AND_CONFIGURATION.md).

## Detection

Startup-time schema validation (schemas/19_configuration_schema.md).

## System response

Process refuses to start; fails loud in the startup log, never starts in a partially-configured state.

## Error code

`N/A (pre-request, process-level)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator fixes the configuration and restarts (operations/02_startup.md).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
