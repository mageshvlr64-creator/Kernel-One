# Model Unavailable

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The configured model runtime process is not running or not reachable.

## Detection

Health check (deployment/13_health_checks.md) and/or a failed connection attempt at call time.

## System response

`MODEL_UNAVAILABLE` (503); circuit breaker opens for that model (runtime/11_retry_policy.md) after 5 consecutive failures in 60s.

## Error code

`MODEL_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Router falls back per features/02_model_router/09_fallback_routing.md; operator alerted via features/25_observability/.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
