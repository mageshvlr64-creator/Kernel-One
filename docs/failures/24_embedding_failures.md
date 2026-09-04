# Embedding Failures

> Failure mode entry. Referenced by the owning feature's "Failure modes" section
> (`docs/features/`) rather than restated there.

## Trigger

The embedding model is unavailable, or produces a vector of the wrong dimension for the configured pgvector column.

## Detection

Dimension check before insert (schemas/08_chunk_schema.md fixed at 768 dimensions for the configured embedding model).

## System response

Document state → `FAILED` at the `INDEXING` stage if embeddings can't be produced; a dimension mismatch is a configuration error (`04_configuration_errors.md`), not a per-document failure.

## Error code

`DEPENDENCY_UNAVAILABLE` (see `reference/01_error_codes.md` for HTTP status and full detail)

## Recovery

Retried per document-processing operation class; a dimension mismatch requires an operator to fix the embedding-model configuration, not a per-document retry.

## Audit requirement

Every occurrence of this failure produces an `AuditEvent` with `result=error` and this
failure's error code, per `schemas/15_audit_event_schema.md` — this applies even to failures
that are ultimately the system behaving correctly (e.g. a correctly-blocked network attempt)
since REQ-AUD-001 makes no exception for "expected" failures.
