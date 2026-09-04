# Release Checklist

> The final gate before any release is tagged, consolidating every testing category above
> into one checklist.

## Checklist

- [ ] All unit/integration/contract/API tests pass (`02..05`).
- [ ] All `SEC-TEST-*` cases pass (`21_security_testing.md`).
- [ ] `TEST-NET-001/002/003` pass on the actual target deployment mode.
- [ ] Demo acceptance testing (`30_demo_acceptance_testing.md`) passes 3x consecutively.
- [ ] No open regression (`29_regression_testing.md`).
- [ ] Performance/load targets met on the target hardware profile (`24`, `25`).
- [ ] Recovery drill performed within the last release cycle (`27_recovery_testing.md`).
- [ ] `reference/14_release_matrix.md`'s gate for the specific milestone being released
      (demo-ready vs. production-ready) is fully satisfied, not partially.
- [ ] `20_DECISION_LOG.md` has no `Decision Required` item that blocks this specific release
      milestone (e.g. DEC-013/014 must be resolved before a production-ready release,
      though not necessarily before a demo-ready one).
