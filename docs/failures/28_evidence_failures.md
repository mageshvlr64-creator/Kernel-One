# Evidence Failures (general)

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The Agent Kernel cannot attach a valid Evidence record to a claim it was about to make.

## Detection

features/14_evidence_and_provenance/09_unsupported_claim_detection.md check before the claim is emitted.

## System response

The claim is not emitted at all — REQ-FUNC-005 requires refusal over fabrication; the agent instead states it could not find supporting evidence for that specific point.

## Error code

`N/A (behavioral requirement, not an HTTP error)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

User can rephrase the question or point the agent at a different document.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
