# Data at Rest

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Sensitive data (documents, audit logs, model weights) stored unencrypted on disk is exposed if the storage medium is physically compromised.

## Where it can occur

PostgreSQL data directory, Object Storage volumes.

## Mitigation

Disk-level encryption (LUKS or equivalent) is a deployment-level requirement for `RESTRICTED`-classification-capable deployments (deployment/14_production_hardening.md) — this is an infrastructure control, not an application-layer one, and is documented as an operator responsibility, not silently assumed.

## Traceability

- Requirements: `REQ-DATA-001`
- Tests: `Verified via deployment checklist, not a runtime SEC-TEST`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
