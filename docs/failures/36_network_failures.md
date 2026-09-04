# Network Failures (infrastructure)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

An *internal* network call (e.g. API to Database) fails — distinct from a blocked *external* call, which is not a failure but correct behavior.

## Detection

Connection-level error handling in each service.

## System response

`DEPENDENCY_UNAVAILABLE`.

## Error code

`DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried per interactive-read/write operation class; sustained failure is an infrastructure incident (operations/10_incident_response.md), not a security incident, unless it correlates with a NETWORK_EGRESS_BLOCKED event (in which case see operations/12_network_incidents.md).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
