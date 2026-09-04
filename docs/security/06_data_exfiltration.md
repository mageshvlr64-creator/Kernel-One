# Data Exfiltration

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

An attempt (via generated code, a malicious tool argument, or a crafted prompt) to move classified data outside the deployment boundary.

## Where it can occur

Code execution sandbox, artifact export, any tool with network-adjacent capability.

## Mitigation

Network egress is denied by default at the container/OS layer regardless of application-layer intent (features/09_code_execution/06_network_isolation.md, REQ-NET-001); artifact export is classification-gated and approval-gated (features/16_human_approval/).

## Traceability

- Requirements: `REQ-NET-001`, `REQ-SEC-002`, `REQ-DATA-001`
- Tests: `SEC-TEST-003`, `SEC-TEST-006`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
