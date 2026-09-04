# Advanced Industrial Intelligence (V2+)

> Explicitly out of V1 scope. This file exists so the boundary is a visible, challengeable
> decision (`02_SCOPE_AND_NON_GOALS.md`), not an implicit gap discovered later.

## What this covers

The V2+ evolution of `industrial/` beyond the V1-committed/V1-aspirational split defined in
`industrial/12_industrial_workflow_boundaries.md`: structured symbol extraction (see
`02_pid_analysis.md`), calculator-grade drawing dimension extraction (`04_drawing_intelligence.md`),
and a proper engineering calculation engine with a formula/standards library
(`03_engineering_calculation_engine.md`).

## Why deferred

Each of these requires either a labeled training/evaluation dataset the project does not yet
have (symbol recognition), a formula/standards library with legal/certification implications
if wrong (calculation engine), or both — none of these are 14-day-build-cycle scope, and
attempting a shallow version risks the exact overclaiming problem
`industrial/11_calculation_verification.md` explicitly warns against.

## Prerequisite before starting V2 work here

A dedicated `benchmarks/` evaluation set for the specific capability (e.g.
`benchmarks/07_visual_benchmark.md` extended with P&ID-specific test images) must exist and
show acceptable accuracy before any V2 capability in this group is presented to a user as more
than a caveated description — the V1-aspirational caveat pattern
(`industrial/09_drawing_understanding.md`) does not get quietly dropped just because a V2
implementation effort has started.
