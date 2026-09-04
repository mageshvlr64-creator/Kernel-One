# Malicious Documents

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

An uploaded file is crafted to exploit a parser vulnerability (e.g. a malformed PDF triggering a buffer overflow in a parsing library) or contains an embedded macro/script.

## Where it can occur

Document Ingestion (features/10_document_ingestion/02_upload_validation.md).

## Mitigation

File type is detected server-side (not trusted from client-supplied MIME header), size-capped, and parsed with libraries kept current per dependency-security scanning (20_dependency_security.md); Office documents' macro content is stripped/ignored, never executed.

## Traceability

- Requirements: not yet mapped to a specific REQ-ID
- Tests: `SEC-TEST-DOC-001 (add to testing/10_document_pipeline_testing.md if not already present)`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
