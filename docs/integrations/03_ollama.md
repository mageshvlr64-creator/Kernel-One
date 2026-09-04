# Ollama Integration

> Secondary inference runtime, used for quick local iteration (PROFILE-A) and as one option
> for CPU/lower-VRAM fallback (DEC-004).

## Contract

Adapter speaks Ollama's native API (`POST /api/generate`, `/api/chat`), normalized to the same
internal contract as the vLLM adapter — callers never know which provider actually served a
given request except via the `Model.provider` field (`schemas/06_model_schema.md`).

## Health check

`GET /api/tags` (lists loaded models) used as the readiness probe.

## Notes

Ollama manages its own model loading/unloading internally; the Model Router's
`is_available` flag is still the source of truth the rest of the system checks, kept in sync
via periodic health polling rather than assuming Ollama's internal state is directly queryable
by other services.
