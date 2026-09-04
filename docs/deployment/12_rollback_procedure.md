# Rollback Procedure

> The explicit reverse of `11_upgrade_procedure.md`, for when an upgrade fails or introduces a
> regression.

## Procedure

1. Stop the new version's services (`03_shutdown.md`).
2. Restore the pre-upgrade backup taken in `11_upgrade_procedure.md` step 2
   (`operations/09_restore_operations.md`).
3. Redeploy the previous version's service images.
4. Run `02_startup.md`, then the demo smoke test, to confirm the rollback restored a working
   state.

## Rule

A rollback is only as good as the backup taken immediately before the upgrade — this is why
`11_upgrade_procedure.md` step 2 is mandatory, not optional, regardless of how confident the
operator is in the new version.
