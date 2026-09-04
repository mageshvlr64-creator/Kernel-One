# Enterprise Identity Integration (V2+)

> Integrating with an external identity provider (LDAP/Active Directory, SAML, or OIDC)
> instead of V1's self-contained `users` table (`schemas/01_database_schema.md`).

## Why not V1

V1's six-role model (`reference/05_permission_matrix.md`) with locally-managed users is
sufficient for the demo and for a single-organization on-prem deployment; enterprise SSO adds
a real external dependency (the identity provider itself) that would need its own
sovereignty/availability analysis before being anything but optional.

## Design constraint this must satisfy if built

Any external identity integration MUST NOT weaken REQ-NET-001/002 — an on-premise LDAP/AD
integration is compatible (internal network only), but a cloud-hosted SSO provider (e.g. a
SaaS OIDC provider) is **categorically excluded** for `air_gapped`/`on_premise` deployments,
and would need explicit gating to `restricted` mode only, with the provider's endpoint added to
the operator's allowlist (`16_ENVIRONMENT_AND_CONFIGURATION.md` `RESTRICTED_MODE_ALLOWLIST`).

## Migration path

The `users.role` enum (`schemas/01_database_schema.md`) would need to map to
externally-provided group claims — this mapping itself becomes a new `Policy`-like
configuration object, following the same operator-configured, centrally-defined pattern as
`domain/16_policy_model.md`, not a one-off integration-specific config format.
