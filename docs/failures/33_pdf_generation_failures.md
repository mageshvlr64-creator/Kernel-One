# PDF Generation Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

Same class of failure, specific to PDF export (e.g. from a DOCX-to-PDF conversion step via LibreOffice, integrations/10_libreoffice.md).

## Detection

Same validation pattern; additionally checks the LibreOffice conversion subprocess's exit code.

## System response

Artifact state → `FAILED`; if LibreOffice itself is unavailable, `DEPENDENCY_UNAVAILABLE`.

## Error code

`TOOL_EXECUTION_FAILED / DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Same as DOCX, plus operator check of the LibreOffice integration's health if the dependency itself is down.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
