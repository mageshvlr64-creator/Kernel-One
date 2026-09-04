# Audit Write Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The audit event insert fails (e.g. database unavailable) at the moment a state-changing action occurs.

## Detection

Transaction wrapping both the primary write and the audit write (REQ-AUD-001).

## System response

The **entire transaction rolls back** — the primary action does not take effect if its audit event cannot be recorded. This is a deliberate, strict choice: an unaudited state change is treated as worse than a failed action.

## Error code

`DEPENDENCY_UNAVAILABLE (surfaced as the action's own failure)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User retries once the database is healthy again; no state was silently changed without a trail.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
