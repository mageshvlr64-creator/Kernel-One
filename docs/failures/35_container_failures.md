# Container Infrastructure Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The container runtime itself (Docker daemon) is unavailable.

## Detection

Health check on the container runtime (deployment/13_health_checks.md).

## System response

`DEPENDENCY_UNAVAILABLE` for any code-execution request; system remains otherwise functional (non-code-execution features unaffected).

## Error code

`DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator restarts the container runtime; alerts fire per features/25_observability/11_alerting.md.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
