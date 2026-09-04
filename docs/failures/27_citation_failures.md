# Citation Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

An Evidence record references a chunk_id or document that no longer exists (e.g. the source document was deleted after the answer was generated).

## Detection

Evidence resolution at display time (api/14_evidence_api.md).

## System response

UI shows 'Source unavailable' distinctly from a broken citation (ui/09_evidence_panel.md) — the claim itself is not retracted, but its verifiability is now degraded and shown as such.

## Error code

`FILE_NOT_FOUND` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Not automatically recoverable once the source is deleted; this is why Document deletion is intentionally soft-delete with a retention window, not immediate hard delete.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
