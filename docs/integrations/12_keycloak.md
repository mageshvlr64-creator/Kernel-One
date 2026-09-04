# Keycloak Integration (V2, not used in V1)

> Listed here as a placeholder for the identity-provider integration described in
> `later/10_enterprise_identity_integration.md` — **not used in V1**, which implements
> authentication directly against the local `users` table
> (`features/19_identity_and_rbac/02_authentication.md`).

## Why this file exists despite being unused

Per this specification's own rule (name deferred capabilities explicitly rather than leaving a
silent gap), Keycloak (or an equivalent OIDC/SAML provider) is the most likely concrete choice
if `later/10_enterprise_identity_integration.md` is ever pursued — recording this here avoids a
future implementer having to reverse-engineer which specific product was intended by
"enterprise identity integration."

## Constraint if ever implemented

Must run on-premise, within the deployment's own network boundary — a cloud-hosted Keycloak
instance would violate REQ-NET-001/002 for `air_gapped`/`on_premise` deployments, per the same
constraint stated in `later/10_enterprise_identity_integration.md`.
