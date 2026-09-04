# llama.cpp Integration

> The CPU-fallback runtime (REQ-AI's `cpu-fallback` capability, DEC-004), and the runtime used
> for `deployment/06_cpu_only_demo.md`.

## Contract

Adapter speaks llama.cpp's server mode HTTP API (`llama-server`'s OpenAI-compatible endpoint),
normalized identically to the vLLM/Ollama adapters.

## Performance note

This is the slowest of the three providers on equivalent hardware (no GPU), which is exactly
why it's scoped to the `cpu-fallback` capability slot and PROFILE-A/`06_cpu_only_demo.md`
rather than being a general-purpose provider choice — see
`performance/02_latency_budgets.md`'s explicit carve-out for this path.
