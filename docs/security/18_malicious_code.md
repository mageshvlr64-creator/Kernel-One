# Malicious Code (agent- or user-submitted)

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Code submitted for execution (by the agent or a user reviewing/editing agent-proposed code) attempts something harmful beyond simple network egress — e.g. fork bombs, disk-filling loops.

## Where it can occur

Code Execution sandbox.

## Mitigation

CPU/memory/process-count/disk-quota limits are enforced by the container runtime, not just a soft application-level check (features/09_code_execution/05_resource_limits.md) — SANDBOX_LIMIT_EXCEEDED is a hard kill, not a warning.

## Traceability

- Requirements: `REQ-SEC-002`
- Tests: `SEC-TEST-003`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
