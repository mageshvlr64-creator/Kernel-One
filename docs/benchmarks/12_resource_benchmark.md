# Resource Benchmark

> Verifies `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`'s VRAM/RAM sizing claims against actual
> measured usage for the pinned model.

## Method

Measure actual VRAM usage (weights + KV cache at realistic context lengths/batch sizes) and
host RAM usage for the candidate model on PROFILE-B hardware; compare against the rough sizing
formula in `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` ("DESIGN LIMIT / rough sizing
guidance") and flag any significant discrepancy.

## Rule

If actual measured usage differs materially from the rough formula's estimate, the formula's
documented status changes from "DESIGN LIMIT" to include the measured correction factor for
that specific model family, rather than leaving future readers to rely on an unverified
formula.
