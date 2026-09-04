# Prompt Injection

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

Malicious instructions embedded in retrieved document content, tool output, or user messages attempt to override system/developer instructions or trigger unauthorized tool calls.

## Where it can occur

Document ingestion, RAG retrieval, tool output relay into agent context.

## Mitigation

Untrusted content is wrapped in a distinct context boundary the agent kernel never treats as instruction-bearing (features/04_agent_kernel/09_observation_handling.md); tool authorization is never granted based on content found inside untrusted context alone.

## Traceability

- Requirements: `REQ-SEC-003`
- Tests: `SEC-TEST-004`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
