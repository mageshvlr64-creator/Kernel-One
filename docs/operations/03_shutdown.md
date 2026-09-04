# Shutdown

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. Stop accepting new Tasks at the API layer (drain mode).
2. Allow in-flight Tasks up to their configured timeout to complete or reach a safe checkpoint (`runtime/14_resume_and_recovery.md`).
3. Stop Agent Kernel and Tool Gateway.
4. Stop Inference Gateway and Model Management.
5. Stop Identity/Policy/Audit services last, after confirming no pending audit writes are in flight.
6. Stop Database and Object Storage.

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
