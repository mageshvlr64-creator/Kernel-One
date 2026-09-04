# Upgrade Procedure

> How to move a running deployment from one version of this system to a newer one.

## Procedure

1. Review the new version's `20_DECISION_LOG.md` entries and `schemas/01_database_schema.md`
   migration additions since the currently-deployed version.
2. Take a verified backup (`operations/08_backup_operations.md`) immediately before upgrading
   — this is the rollback point if the upgrade fails.
3. Apply database migrations (forward-only, per the migration policy in
   `schemas/01_database_schema.md`) — never edit an already-applied migration.
4. Deploy new service images following the same startup order as `operations/02_startup.md`.
5. Run the demo smoke test (`demo/01_demo_overview.md`) before declaring the upgrade complete.

## Zero-downtime consideration

V1's single-node architecture (DEC-001) does not support zero-downtime upgrades — an upgrade
is a planned maintenance window (`operations/03_shutdown.md` → upgrade → `02_startup.md`).
Zero-downtime rolling upgrades are a `later/08_multi_node_scaling.md`-adjacent V2 capability.
