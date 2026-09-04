# OCR Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

OCR engine crashes, times out, or produces zero-confidence output for a page.

## Detection

OCR stage error handling (features/11_ocr/09_ocr_failures.md); confidence threshold check.

## System response

Page marked with `ocr_confidence=null` or a very low score rather than silently treated as successfully extracted; document-level failure only if OCR is unavailable entirely (`DEPENDENCY_UNAVAILABLE`).

## Error code

`DEPENDENCY_UNAVAILABLE (engine down) / low-confidence flag (not a hard failure)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Low-confidence pages are still indexed but flagged (industrial/02_inspection_reports.md); engine-down failures retry per document-processing operation class.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
