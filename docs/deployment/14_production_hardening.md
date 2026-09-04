# Production Hardening

> Additional controls layered on top of the base deployment procedures above, required before
> treating a deployment as production-grade (as opposed to a demo/pilot).

## Checklist

- [ ] Disk-level encryption enabled on Database and Object Storage volumes
      (`security/23_data_at_rest.md`), especially for deployments handling `CONFIDENTIAL`/`RESTRICTED`
      classification data.
- [ ] TLS enabled for any multi-host traffic (`security/24_data_in_transit.md`).
- [ ] Backup verification (`operations/08_backup_operations.md`) has run successfully at least
      once, not just configured.
- [ ] A disaster-recovery drill (`operations/13_disaster_recovery.md`'s "required drill") has
      been performed.
- [ ] `DEC-013`/`DEC-014` resolved — model checkpoints pinned and performance numbers
      benchmark-verified, not left as DESIGN LIMIT placeholders (`20_DECISION_LOG.md`).
- [ ] `REQ-PERF-002` (concurrent user target) answered and the deployment's hardware profile
      (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`) sized against it.
- [ ] All `SEC-TEST-###` cases (`testing/21_security_testing.md`) pass against the actual
      production build, not just a development build.

## Rule

None of the demo-only allowances (e.g. `06_cpu_only_demo.md`'s relaxed performance target, or
`02_local_development.md`'s temporary `restricted` mode for setup) apply once this checklist
is being evaluated — production hardening assumes the full, real deployment posture.
