# Data in Transit

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Traffic between internal services, or between the UI and API, is intercepted.

## Where it can occur

All internal service-to-service and UI-to-API traffic.

## Mitigation

TLS is required for UI-to-API traffic in any multi-host deployment (PROFILE-C/D); for single-node V1 (PROFILE-B, all services on `localhost`), TLS is optional but recommended — this distinction is a documented, not silent, tradeoff.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `Verified via deployment checklist`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
