# RAG Authorization Bypass

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A query is crafted to retrieve content from a document above the caller's clearance, by manipulating search terms or exploiting a post-hoc (rather than pre-ranking) filter.

## Where it can occur

Knowledge Fabric retrieval (features/13_knowledge_fabric/12_permission_filtering.md).

## Mitigation

Classification and workspace filters are applied in the database query itself, before ranking/scoring — never as a post-retrieval filter that could be bypassed by a sufficiently specific query (REQ-FUNC-004).

## Traceability

- Requirements: `REQ-FUNC-004`
- Tests: `SEC-TEST-001`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
