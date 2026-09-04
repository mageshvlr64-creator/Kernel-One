# Integration Failure Policy

> The shared rule every integration file above follows for handling that specific
> third-party dependency's failure — referenced rather than restated per-integration.

## Policy

1. **Every integration failure maps to a named entry in `docs/failures/`** — no integration's
   failure is "just an exception" without a documented response (e.g. vLLM failures →
   `failures/10_model_unavailable.md`; PostgreSQL failures → `failures/19_database_failures.md`).
2. **Every integration is wrapped in an adapter** (`01_integration_architecture.md`) that is
   the sole point of contact with that dependency — failures are caught and translated to the
   canonical error registry (`reference/01_error_codes.md`) at the adapter boundary, not left
   as raw third-party exceptions propagating into business logic.
3. **No integration's failure silently degrades security or sovereignty guarantees** — e.g. if
   the Audit Service's database write fails, the action itself fails too (REQ-AUD-001,
   `failures/40_audit_failures.md`), rather than the integration failure being "worked around"
   by skipping the audit step.
4. **Health checks exist for every integration with a runtime dependency** (all except
   build-time-only integrations like dependency scanning) and feed
   `deployment/13_health_checks.md`'s readiness composition.
