# Release Matrix (Reference)

> Which requirements/features must be true for a build to be called "V1 demo-ready" vs.
> "V1 production-ready" vs. "V2."

| Milestone | Gate |
|---|---|
| **Demo-ready** | `08_BUILD_PHASES.md` Phase 10 exit criteria: full demo runbook (`demo/01_demo_overview.md`) passes 3x consecutively on PROFILE-B; all P0 requirements (`03_REQUIREMENTS.md`) implemented; DEC-006's two rehearsed roles work end-to-end |
| **Production-ready** | All of the above, plus `deployment/14_production_hardening.md`'s full checklist, including DEC-013/DEC-014 resolved (benchmarked, not just labeled) and `REQ-PERF-002` answered |
| **V2 candidate** | Any capability in `later/` — requires a new REQ-ID, a new decision log entry scoping it, and its own benchmark/evaluation gate before being presented as anything more than a caveated description (per `industrial/12_industrial_workflow_boundaries.md`'s pattern, generalized) |

## Rule

A build is never called "production-ready" on the strength of passing the demo alone — the
demo gate and the production gate are deliberately different bars, per this table.
