# Recovery Testing

> Verifies `operations/09_restore_operations.md` and `13_disaster_recovery.md` actually work,
> beyond the automated nightly verification in `08_backup_operations.md`.

## Required tests

- Full disaster-recovery drill (per `13_disaster_recovery.md`'s "required drill"): restore a
  backup to a scratch environment, run the demo smoke test against it, confirm success.
- Point-in-time restore (if WAL archiving is configured): restore to a specific timestamp,
  verify data matches expectations as of that exact time.
- Audit hash-chain verification on the restored copy — a restore is not considered "passed"
  if the chain doesn't validate (REQ-SEC-005).
