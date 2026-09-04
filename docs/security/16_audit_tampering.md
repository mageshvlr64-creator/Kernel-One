# Audit Tampering

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

An attempt to modify or delete a past audit event to hide an action.

## Where it can occur

Audit Service (features/17_audit/), direct database access.

## Mitigation

`audit_events` table has `UPDATE`/`DELETE` revoked for all application roles at the database level (REQ-SEC-005); a hash chain makes any out-of-band tampering (e.g. via a superuser DB connection) detectable by the integrity job (operations/05_log_management.md).

## Traceability

- Requirements: `REQ-SEC-005`
- Tests: `TEST-AUDIT-002`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
