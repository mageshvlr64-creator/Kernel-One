# Model Router Testing

> Covers `features/02_model_router/` — capability matching, resource fit, and fallback.

## Required tests (referenced by REQ-AI-001/003)

- `TEST-ROUTER-004`: swapping a capability slot's backing model via registry config only (no
  code change) still routes correctly.
- `TEST-ROUTER-005`: an MoE model whose `total_parameters` storage exceeds available VRAM is
  rejected by the hardware-fit check even when `active_parameters_per_token` would fit
  (REQ-AI-003's exact confusion this guards against).
- Fallback: primary model marked `is_available=false` → router selects the configured
  fallback for that capability slot, not a hard failure.
