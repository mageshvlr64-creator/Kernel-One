# Supply Chain Security

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A compromised upstream package, model checkpoint, or base image is introduced into the build.

## Where it can occur

Model Management (checkpoint provenance), package installation, base images.

## Mitigation

Model checkpoints are verified against a published checksum before registration (features/01_model_management/05_model_installation.md); packages are installed from a pinned lockfile, not floating version ranges, in `air_gapped`/`on_premise` builds sourced from an internal mirror, never a live public registry at deploy time.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `Build-time provenance check, not a runtime SEC-TEST`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
