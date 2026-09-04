# Model Capability Matrix (Reference)

> Restates `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s reference model registry as a
> capability-focused quick lookup.

| Capability slot | Requires | Fallback if unavailable |
|---|---|---|
| `general-reasoning` | A model with this capability tag (`schemas/06_model_schema.md`) | `cpu-fallback` |
| `coding` | A model with `coding` capability tag | `general-reasoning` (degraded — see `features/02_model_router/09_fallback_routing.md`) |
| `vision` | A model with `vision` capability tag | None in V1 — a vision-requiring request fails with `MODEL_UNAVAILABLE` if no vision model is configured, rather than silently attempting a text-only model against an image |
| `tool_calling` | A model with `tool_calling` capability tag | Required for `features/04_agent_kernel/` — no fallback; a model lacking this capability cannot serve as the planning model |
| `structured_output` | A model with `structured_output` capability tag | Falls back to prompt-engineered JSON extraction with stricter validation, if no structured-output-capable model is configured |
| `cpu-fallback` | The designated 3-4B CPU-viable model | None — this is itself the fallback of last resort |

## Full sizing detail

See `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` for VRAM math and the MoE storage-vs-active
distinction (REQ-AI-003) — this file is the capability-to-fallback mapping only.
