# CPU-Only Demo (Fallback)

> The degraded-but-functional path for PROFILE-A or a PROFILE-B host without a working GPU —
> REQ-AI's `cpu-fallback` capability requirement realized as an actual deployment option.

## What changes

Only the `cpu-fallback` capability slot (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`, a 3–4B
heavily-quantized model) is registered; the Model Router has no larger-model fallback to route
to, so every request uses this smaller model.

## Expected impact

Slower responses (CPU inference is meaningfully slower than GPU, `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s
CPU-offloading note) and somewhat lower answer quality (smaller model) — this is an accepted,
documented tradeoff for demo continuity, not a silent failure. `REQ-PERF-001`'s 5-minute
target explicitly does NOT apply to this fallback path — it's PROFILE-B's target only.

## When to use this

As a rehearsal fallback if the primary demo hardware's GPU is unavailable on the day, per
`demo/13_failure_demo.md`'s recovery planning — not as the primary demo path.
