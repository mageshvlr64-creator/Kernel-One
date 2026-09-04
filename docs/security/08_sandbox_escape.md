# Sandbox Escape

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Generated code attempts to break out of its container (e.g. via a kernel exploit, mounted-volume traversal, or privileged syscall).

## Where it can occur

Code Execution (features/09_code_execution/).

## Mitigation

Container runs as non-root, with a minimal capability set (no CAP_SYS_ADMIN etc.), read-only root filesystem except the task-scoped workspace mount, and no privileged mode (DEC-005). Escapes are a Sev1 incident per operations/11_security_incidents.md regardless of whether they were 'just a test.'

## Traceability

- Requirements: `REQ-SEC-002`
- Tests: `SEC-TEST-003`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
