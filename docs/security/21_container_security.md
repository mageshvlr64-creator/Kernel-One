# Container Security

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A container (sandbox or a core service) is misconfigured in a way that widens its blast radius beyond intent — e.g. an unnecessary privileged flag, an overly broad volume mount.

## Where it can occur

All containerized services, especially Code Execution.

## Mitigation

Containers run non-root, minimal capability set, `--network=none` where applicable, and only the specific volume mounts each service needs (never the full host filesystem) — reviewed as part of 08_BUILD_PHASES.md Phase 4/8 exit criteria.

## Traceability

- Requirements: `REQ-SEC-002`
- Tests: `SEC-TEST-003`, `SEC-TEST-005`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
