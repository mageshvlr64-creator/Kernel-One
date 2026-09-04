# Performance Testing

> Verifies the budgets in `docs/performance/` against real measurements — the mechanism that
> eventually resolves DEC-014's pending benchmark validation.

## Method

Automated load-generation scripts exercise each operation class (`runtime/11_retry_policy.md`)
at realistic volumes on the target hardware profile, recording p50/p95/p99 latency and
comparing against `performance/02_latency_budgets.md`'s targets.

## Rule

A performance regression (p95 exceeding budget by more than 20%, CONFIG DEFAULT threshold) is
treated as a build-blocking defect in `08_BUILD_PHASES.md` Phase 9/10, not a "known slow"
acceptable state — unless the budget itself is revised (with a `20_DECISION_LOG.md` entry
explaining why).
