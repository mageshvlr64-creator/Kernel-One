# Retrieval Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The vector index or keyword index is unreachable, or a query times out.

## Detection

Knowledge Fabric's query error handling (features/13_knowledge_fabric/15_retrieval_failures.md).

## System response

`RAG_INDEX_UNAVAILABLE` (503).

## Error code

`RAG_INDEX_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried per interactive-read operation class; if sustained, the agent surfaces 'search is temporarily unavailable' rather than fabricating an answer without retrieval.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
