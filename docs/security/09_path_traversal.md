# Path Traversal

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

A filesystem tool call attempts to read/write outside its authorized workspace root via `../` sequences or symlinks.

## Where it can occur

Filesystem Tool (features/06_filesystem_tool/).

## Mitigation

Every path is resolved to a canonical absolute path and checked against the workspace root boundary before any I/O; symlinks are resolved and re-checked, not trusted at face value (features/06_filesystem_tool/06_symlink_protection.md).

## Traceability

- Requirements: `REQ-SEC-004`
- Tests: `SEC-TEST-005`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
