# Hardware Profiles and Resource Model (Canonical)

> **Canonical owner** of hardware/resource assumptions. `docs/07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`
> holds this content directly; other documents reference a `PROFILE-X` name.

## Profiles

| | PROFILE-A — Dev workstation | PROFILE-B — Reference demo | PROFILE-C — Production single-node | PROFILE-D — Larger enterprise |
|---|---|---|---|---|
| CPU | 6+ core consumer (e.g. Ryzen 5 / i5, 12th-gen+) | 8+ core (e.g. Ryzen 7 / i7) | 16+ core server-class | 32+ core, dual-socket optional |
| RAM | 16 GB | 32 GB | 64–128 GB | 256 GB+ |
| GPU | Optional; none required | 1× 12–16GB VRAM consumer GPU (e.g. RTX 4060 Ti 16GB / RTX 4070) | 1× 24–48GB VRAM (e.g. RTX 4090 / L40S / A6000) | 2–8× 80GB VRAM (A100/H100 class) |
| VRAM | 0–8 GB | 12–16 GB | 24–48 GB | 80GB+ per GPU |
| Storage | 512 GB NVMe SSD | 1 TB NVMe SSD | 2–4 TB NVMe SSD, RAID1 recommended | 8TB+ NVMe, RAID + object storage tier |
| Network | N/A (fully offline capable) | N/A (fully offline capable) | Internal LAN only (`on_premise` mode) | Internal LAN + internal registry mirror |
| Expected model class | 3B–8B, 4-bit quantized, CPU or light-GPU offload | 7B–14B, 4-bit/8-bit quantized, GPU-resident | 14B–34B dense or MoE with ≤14B active, GPU-resident | 34B–70B+ dense, or MoE with ≤40B active, multi-GPU |
| Expected concurrency | 1 user | 1–3 users | 5–20 users | 20–100+ users |
| Expected latency (text, p50) | 3–8s first token | 1–3s first token | < 1.5s first token | < 1s first token |
| Known limitations | No vision model concurrently with a text model; OCR is slow (CPU) | Vision model must be swapped in/out of VRAM with text model unless VRAM ≥ 16GB allows both quantized | Multi-user queuing required beyond ~5 concurrent inference calls | Requires the multi-node architecture (`architecture/16_multi_node_architecture.md`) — **REQ-DEP-004 DECISION REQUIRED** on whether this is V1 or V2 |

**V1 reference target is PROFILE-B.** The demo (`docs/demo/`) is scripted and load-tested
against PROFILE-B only; PROFILE-A must run the demo but may be slower (no latency guarantee);
PROFILE-C/D are documented for production planning but are not part of the V1 demo commitment.

## Model-resource math the router and operators must apply correctly

- **Dense model VRAM (4-bit quant, inference only, rough):** `≈ parameters_in_billions × 0.6 GB`
  (e.g. a 7B dense model at 4-bit ≈ 4.2GB weights) **plus** KV cache, which scales with
  context length × batch size × layer count — for a 7B model at 8K context this typically adds
  1–3GB. Treat this formula as **DESIGN LIMIT / rough sizing guidance**, not a benchmarked
  constant — always validate against the specific runtime's own reported memory usage.
- **MoE storage vs. active compute (REQ-AI-003):** an MoE model's **disk and VRAM storage
  requirement is driven by `total_parameters`** (all experts must be resident/loadable), while
  its **per-token compute cost is driven by `active_parameters_per_token`**. A 47B-total /
  13B-active MoE model still needs storage/VRAM sized for ~47B parameters, not 13B — the router
  MUST evaluate hardware fit against `total_parameters`.
- **Multimodal overhead:** vision-capable models typically add 10–30% VRAM overhead for the
  vision encoder plus per-image token cost (varies by resolution/tiling scheme) — treat any
  specific number here as model-specific and sourced from that model's own card, not assumed.
- **Context length / KV cache:** KV cache size scales roughly linearly with context length;
  doubling context roughly doubles KV cache VRAM for a fixed batch size. This is why
  `model-inference` timeout in `runtime/11_retry_policy.md` differentiates text vs. vision/long
  context.
- **CPU offloading:** layers not fitting in VRAM can be offloaded to CPU/RAM at a substantial
  latency cost (often 3–10× slower per token); acceptable for PROFILE-A background/batch use,
  not acceptable for the interactive PROFILE-B demo.

## Reference model registry (V1 candidates)

> Populated with real, currently-available open-weight model families as of the last
> documentation pass. **Exact model checkpoint/version pinning is a `DECISION REQUIRED`** item
> (`20_DECISION_LOG.md` DEC-013) — the entries below define the *capability class* the router
> depends on; the specific checkpoint is a deployment-time configuration value in
> `features/01_model_management/01_model_registry.md`, not hardcoded here.

| Capability slot | Model class (example family) | Approx. total params | Approx. active params (if MoE) | Quantization | VRAM (4-bit) | Context | Fits |
|---|---|---|---|---|---|---|---|
| `general-reasoning` (default) | 7B–8B dense instruction-tuned open-weight model | 7–8B | N/A (dense) | 4-bit (GGUF/AWQ) | ~5–6 GB | 8K–32K depending on checkpoint | PROFILE-B+ |
| `coding` | 7B–14B dense, code-tuned open-weight model | 7–14B | N/A (dense) | 4-bit | ~5–9 GB | 16K–32K | PROFILE-B+ |
| `vision` (multimodal) | 7B–8B vision-language open-weight model | 7–8B + vision encoder | N/A (dense) | 4-bit | ~6–8 GB | 8K (text) + image tokens | PROFILE-B (may require swap with text model on 12–16GB VRAM) |
| `large-context / production` | MoE open-weight model, larger total/active footprint | 40B+ total | 12–14B active | 4-bit | 25–40 GB+ | 32K+ | PROFILE-C/D only |
| `cpu-fallback` | 3B–4B dense, heavily quantized | 3–4B | N/A (dense) | 4-bit | CPU/RAM only, ~2–3GB RAM | 4K–8K | PROFILE-A, or PROFILE-B/C fallback when GPU unavailable |

Each row corresponds to a `ModelCapability` in the domain model
(`domain/08_model_provider_model.md`); the router (`features/02_model_router/`) selects a
capability slot, and the model registry resolves that slot to the currently-configured
checkpoint. Swapping a checkpoint is a registry update, not a code or router change
(REQ-AI-001).

## V1 resource-constrained strategy

- V1 MUST be demonstrable on PROFILE-B (a single consumer GPU workstation).
- V1 MUST support a `cpu-fallback` capability so the demo degrades gracefully (slower, not
  broken) if run on PROFILE-A or if the GPU is unavailable.
- The router MUST NOT assume any specific model checkpoint is present; absence of a configured
  capability slot's model returns `MODEL_UNAVAILABLE` and triggers fallback routing
  (`features/02_model_router/09_fallback_routing.md`), never a crash.
