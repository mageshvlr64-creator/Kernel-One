# Authorization Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Authenticated caller lacks the role/policy/classification/approval condition for the requested action.

## Detection

Policy Engine evaluation (features/21_policy_engine/03_policy_evaluation.md) before the action executes.

## System response

`POLICY_DENIED`, `TOOL_NOT_ALLOWED`, or `FILE_CLASSIFICATION_DENIED` depending on which condition failed (403).

## Error code

`POLICY_DENIED / TOOL_NOT_ALLOWED / FILE_CLASSIFICATION_DENIED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User requests role/access change through an out-of-band process (not automatable, by design — REQ-SEC-001).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
