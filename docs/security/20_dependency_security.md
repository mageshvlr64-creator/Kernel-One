# Dependency Security

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A third-party library (Python/Node package, container base image) has a known vulnerability.

## Where it can occur

Every service in services/ and packages/ (15_CODEBASE_TARGET_STRUCTURE.md).

## Mitigation

Automated dependency scanning (e.g. `pip-audit`/`npm audit` equivalent) runs in CI (08_BUILD_PHASES.md Phase 0 tooling); base images pinned to specific digests, not floating `latest` tags, so a compromised upstream image doesn't silently propagate.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `CI dependency-scan gate, not a runtime SEC-TEST`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
