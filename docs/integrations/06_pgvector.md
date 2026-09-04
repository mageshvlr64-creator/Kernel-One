# pgvector Integration

> The vector-search extension to PostgreSQL (DEC-002), specifically for
> `document_chunks.embedding` (`schemas/01_database_schema.md`).

## Index type

HNSW (`CREATE INDEX ... USING hnsw`), chosen over IVFFlat for better recall at V1's expected
corpus size without requiring a separate training/build step that IVFFlat needs — this
tradeoff is documented here rather than left implicit in the DDL comment alone.

## Distance metric

Cosine distance (`vector_cosine_ops`), matching the embedding model's training objective —
changing the embedding model (`features/01_model_management/`) without re-verifying this
metric choice is still appropriate is a `DECISION REQUIRED`-worthy check, not an assumed-safe
swap.

## Scaling boundary

See `performance/12_scaling_limits.md` for where pgvector's practical performance ceiling sits
relative to V1's expected corpus size.
