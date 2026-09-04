# DOCX Generation Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The generated DOCX fails to open correctly, or the templating library throws an error on specific content (e.g. an unusual table structure).

## Detection

Structural validation stage (runtime/_state_machines_canonical.md#artifact VALIDATING state) — the file is actually opened/parsed programmatically to confirm validity before being marked READY.

## System response

Artifact state → `FAILED` rather than delivering a corrupt file to the user.

## Error code

`TOOL_EXECUTION_FAILED` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried once; persistent failure logged for engineering follow-up (the specific content that broke templating is a real bug to fix, not a permanent limitation).

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
