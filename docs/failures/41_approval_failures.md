# Approval Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

An approval decision fails to record (e.g. race with expiry), or an already-decided approval receives a second decision.

## Detection

State machine guard on the Approval entity (runtime/_state_machines_canonical.md#approval).

## System response

`RESOURCE_CONFLICT` (409) for a double-decision attempt; expiry is handled by a scheduled job transitioning `REQUESTED` → `EXPIRED` after `APPROVAL_EXPIRY_HOURS`.

## Error code

`RESOURCE_CONFLICT` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Requester creates a new Approval request if the original expired; a double-decision attempt is simply rejected, first decision stands.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
