# Model Operations (load/replace)

> Operational runbook. Concrete, ordered steps — not a description of what the feature does
> (see the relevant `docs/features/` file for that).

## Procedure

1. To add a model: add an entry via `POST /api/v1/models` (Administrator/Operator), place weights at the configured path, verify health check passes.
2. To replace a model backing a capability slot: add the new model, verify its health check, update the capability→model mapping in the registry, then mark the old model `is_available=false` — never delete a model row referenced by any Task's `agent_runs.model_id` history (REQ-AUD-001 traceability).
3. To remove a model entirely: confirm no active Task references it, then `DELETE /api/v1/models/{id}` — fails with `RESOURCE_CONFLICT` otherwise.

## Related

- `docs/deployment/13_health_checks.md`
- `docs/09_BUILD_ORDER.md`
- `docs/operations/01_operator_guide.md`
