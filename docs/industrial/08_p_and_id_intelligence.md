# P&ID Intelligence

> Piping and Instrumentation Diagram understanding — **V1-aspirational, not demo-committed.**
> See `12_industrial_workflow_boundaries.md` for the explicit scope line, and
> `later/02_pid_analysis.md` for the fuller V2 treatment this capability graduates into.

## What V1 can realistically do

`features/12_multimodal/` lets a vision-capable model describe a P&ID image in general terms
(equipment types visible, apparent flow direction if visually obvious) — this is a
**description**, not a structured symbol-recognition extraction. The agent explicitly states
this limitation rather than presenting a general visual description as equivalent to a proper
P&ID symbol/tag extraction.

## What V1 explicitly does not do

- Extract a structured equipment tag list with cross-references to a tag database.
- Verify P&ID consistency against actual piping (requires a symbol library and rule engine
  not built for V1 — tracked in `later/02_pid_analysis.md`).

## Why this is safe to defer

The demo scenario (`workflows/01_inspection_report.md`) does not require P&ID understanding;
deferring this avoids overclaiming a capability that would need dedicated evaluation
(`benchmarks/07_visual_benchmark.md`) before being demo-safe.
