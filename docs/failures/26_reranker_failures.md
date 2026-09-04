# Reranker Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The reranking step (features/13_knowledge_fabric/10_reranking.md) fails or times out.

## Detection

Reranker call error handling.

## System response

Falls back to the pre-rerank hybrid-search ranking rather than failing the whole retrieval — reranking is a quality improvement, not a hard dependency of retrieval succeeding at all.

## Error code

`N/A (graceful degradation, not a hard error)` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Logged as a degraded-quality event (features/25_observability/) even though the request itself succeeds.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
