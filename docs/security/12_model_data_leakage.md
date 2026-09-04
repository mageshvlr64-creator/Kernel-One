# Model Data Leakage

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Content from one workspace/classification level leaks into a response for a different workspace/user via shared model context, cache, or memory.

## Where it can occur

Agent Memory (features/22_agent_memory/), Inference Gateway request batching.

## Mitigation

MemoryEntry rows are scoped and permission-filtered identically to Documents (features/22_agent_memory/09_memory_permissions.md); the Inference Gateway never batches requests from different workspaces into a shared context window.

## Traceability

- Requirements: `REQ-DATA-001`
- Tests: `TEST-MEMORY-001 (see testing/09_rag_testing.md)`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
