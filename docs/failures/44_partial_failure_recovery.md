# Partial Failure Recovery (cross-cutting)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Any multi-step operation (a Task's Plan, a multi-file artifact generation, a multi-document ingestion batch) fails partway through.

## Detection

Each step's own state machine tracks completion independently (runtime/_state_machines_canonical.md) — there is no single 'overall operation' row whose partial state is ambiguous.

## System response

Completed steps' state changes stand (they were each individually transactional and audited); the failed step and anything depending on it are marked `FAILED`/`CANCELLED`; nothing is left in an indeterminate state.

## Error code

`Varies by which step failed — see that step's own failure file` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

The Agent Kernel's replanning logic (features/04_agent_kernel/10_replanning.md) decides whether to resume from the failure point or restart — this is the general pattern every other 'stuck partway' failure in this directory follows.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
