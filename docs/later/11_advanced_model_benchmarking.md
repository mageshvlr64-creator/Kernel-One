# Advanced Model Benchmarking (V2+)

> A more rigorous successor to the reference model registry's currently-informal sizing
> guidance (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) and the DEC-013/DEC-014 pending
> benchmark validation.

## What V1 has

Rough, labeled (CONFIG DEFAULT/DESIGN LIMIT) sizing formulas and a small reference model
registry — enough to make a reasonable V1 choice, explicitly not yet empirically validated.

## What this V2 item would add

- An automated benchmark harness (`benchmarks/01_benchmark_overview.md` through
  `14_router_scoring.md` — currently specification-only) that actually runs candidate models
  against `benchmarks/02_benchmark_dataset.md` and produces real, reproducible numbers to
  replace every DESIGN LIMIT/CONFIG DEFAULT label with a BENCHMARKED one.
- A regression suite that re-runs benchmarks whenever a new model checkpoint is registered
  (`features/01_model_management/`), preventing an undocumented model swap from silently
  degrading routing quality.

## Why not V1

Building a real benchmark harness and dataset is itself a substantial effort — V1 accepts
labeled-but-unverified defaults specifically so the 14-day build isn't blocked on this, per
the precision-labeling discipline established throughout this specification (rather than
either fabricating benchmark numbers or blocking on a proper harness).
