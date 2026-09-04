# Denial of Service

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A user or automated client floods the API with requests, or submits a task designed to consume disproportionate model/tool resources.

## Where it can occur

API layer, Agent Kernel (unbounded replanning), Inference Gateway.

## Mitigation

Rate limiting per user (schemas/02_api_schema.md, RATE_LIMITED); AGENT_MAX_STEPS/AGENT_MAX_REPLANS caps (16_ENVIRONMENT_AND_CONFIGURATION.md) bound any single task's resource consumption regardless of how the model behaves.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `TEST-PERF-DOS-001 (add to testing/25_load_testing.md if not already present)`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
