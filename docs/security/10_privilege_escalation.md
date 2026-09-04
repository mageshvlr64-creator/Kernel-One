# Privilege Escalation

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A lower-privileged user or a compromised session attempts to gain Administrator-level capability (e.g. by manipulating a client-supplied role field, or exploiting a missing server-side check).

## Where it can occur

Any API endpoint, especially User/Role management (api/03_users_api.md) and Policy management (api/20_policy_api.md).

## Mitigation

Role and clearance are read from the authenticated session server-side, never accepted from client-supplied request fields (REQ-SEC-001); role/policy changes themselves require Administrator and are fully audited.

## Traceability

- Requirements: `REQ-SEC-001`
- Tests: `SEC-TEST-002`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
