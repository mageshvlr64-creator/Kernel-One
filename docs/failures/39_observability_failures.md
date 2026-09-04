# Observability Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The metrics/logging/tracing pipeline itself fails (e.g. OpenTelemetry collector unreachable).

## Detection

Instrumentation library's own error handling — designed to never block the request it's instrumenting.

## System response

The observed request still succeeds; the specific log line/metric/trace for it is dropped and this drop is itself counted (a 'telemetry gap' counter) so operators know observability coverage temporarily degraded.

## Error code

`N/A (never surfaced to the end user)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Operator restarts the collector; historical gap remains a known blind spot for that window, not silently backfilled with fabricated data.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
