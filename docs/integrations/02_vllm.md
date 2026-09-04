# vLLM Integration

> Primary inference runtime for GPU-resident models (DEC-004).

## Contract

The adapter (`services/inference-gateway/adapters/vllm.py` per
`15_CODEBASE_TARGET_STRUCTURE.md`) speaks vLLM's OpenAI-compatible HTTP API
(`POST /v1/chat/completions`, `/v1/completions`), normalized to the internal
`schemas/06_model_schema.md` contract before returning to callers.

## Health check

`GET /health` on the vLLM server, used by `deployment/13_health_checks.md`'s readiness check
for any capability slot backed by this provider.

## Failure modes specific to this integration

Model load failures (insufficient VRAM, corrupt checkpoint) surface as `MODEL_UNAVAILABLE`
(`failures/10_model_unavailable.md`); vLLM's own OOM errors surface as
`MODEL_RESOURCE_EXHAUSTED` (`failures/09_model_oom.md`).
