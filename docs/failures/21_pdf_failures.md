# PDF Parsing Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

A PDF is corrupted, password-protected, or uses an unsupported feature the parser can't handle.

## Detection

PDF parsing library's error/exception during features/10_document_ingestion/04_native_pdf_parsing.md.

## System response

Document state → `FAILED`, `INVALID_REQUEST` with a specific reason ('password-protected PDFs are not supported' etc.), not a generic parse error.

## Error code

`INVALID_REQUEST` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User removes password protection or provides an alternative format.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
