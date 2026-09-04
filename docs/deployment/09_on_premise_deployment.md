# On-Premise Deployment

> Concrete deployment procedure for `NETWORK_MODE=on_premise`
> (`architecture/19_on_premise_architecture.md`).

## Procedure

1. Deploy within the organization's internal network, with outbound firewall rules permitting
   traffic only to other internal hosts/subnets (never a public-internet route) — this is
   typically an existing organizational network policy the deployment integrates with, rather
   than a bespoke allowlist per `08_restricted_network_deployment.md`.
2. If integrating with internal services (log aggregation, LDAP — the latter only if
   `later/10_enterprise_identity_integration.md` is eventually built), document each
   integration's specific network requirement explicitly.
3. Set `NETWORK_MODE=on_premise`, run `02_startup.md`.
4. Verify via the Network Sovereignty Panel that public-internet reachability specifically is
   blocked, distinct from verifying zero reachability entirely (which would be incorrect for
   this mode).

## Distinction to communicate to the operator

This mode is the least restrictive of the three, but still has a hard, verified guarantee: no
public internet egress, ever — this should be stated plainly in any deployment sign-off
documentation so "on-premise" isn't mistaken for "no sovereignty guarantee at all."
