# Tool Abuse

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A model-generated plan attempts to invoke a tool outside its authorized risk/role band, or chains low-risk tools to achieve a high-risk effect.

## Where it can occur

Tool Gateway, Agent Kernel planning.

## Mitigation

Every tool invocation is independently authorized at call time, not just at plan-generation time (features/05_tool_gateway/04_tool_permissions.md) — a chain of low-risk calls does not inherit a higher authorization than each individual call earns.

## Traceability

- Requirements: `REQ-SEC-001`
- Tests: `SEC-TEST-002`, `SEC-TEST-007`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
