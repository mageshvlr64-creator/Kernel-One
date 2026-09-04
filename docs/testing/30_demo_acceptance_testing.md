# Demo Acceptance Testing

> The specific test suite gating `08_BUILD_PHASES.md` Phase 10 / `reference/14_release_matrix.md`'s
> demo-ready milestone.

## Required passes (all three, consecutively, no manual intervention beyond scripted
## approvals)

1. Full `demo/01_demo_overview.md` primary scenario, timed against `REQ-PERF-001`'s target.
2. `demo/06_coding_agent_demo.md` secondary scenario.
3. `demo/07_multimodal_demo.md` secondary scenario, if included in the planned walkthrough.

## Rehearsal requirement

Per `demo/13_failure_demo.md`, at least one full rehearsal on the actual demo hardware
(not just CI infrastructure) is required before the live demo — a passing CI run alone does
not satisfy this gate, since hardware-specific issues (GPU driver quirks, actual network
disconnection behavior) only surface on real hardware.
