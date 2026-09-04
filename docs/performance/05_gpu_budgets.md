# GPU (VRAM) Budgets

> Restates and cross-references `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s model-sizing
> section specifically as a performance-budget concern (this file is the pointer; that file
> is the canonical sizing math, MoE storage-vs-active-parameter distinction, and reference
> registry — not restated here).

## Budget allocation for PROFILE-B (12-16GB VRAM)

| Allocation | Approx. VRAM | Notes |
|---|---|---|
| `general-reasoning`/`coding` capability model (7-8B, 4-bit) | 5-9GB | See `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` reference registry |
| `vision` capability model, if co-resident | 6-8GB | May require swap-in/swap-out with the text model if combined footprint exceeds available VRAM (`deployment/05_gpu_server.md`) |
| KV cache headroom | 1-3GB | Scales with context length × concurrent requests |
| Reserved headroom (driver overhead, fragmentation) | ~1GB | CONFIG DEFAULT safety margin |

## Rule

See `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` for the authoritative math (MoE total vs.
active parameters, REQ-AI-003) — this file only restates it as a performance-budget line item.
