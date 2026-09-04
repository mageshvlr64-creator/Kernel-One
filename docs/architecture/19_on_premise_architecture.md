# On-Premise Architecture

> The `NETWORK_MODE=on_premise` realization of `11_network_boundaries.md`.

## Defining property

Outbound connectivity permitted within the organization's own network (e.g. reaching an
internal LDAP server for `later/10_enterprise_identity_integration.md`, if ever built, or an
internal logging aggregator) but never the public internet.

## Distinction from `restricted`

`restricted` mode's allowlist is a short, explicit, audited list of specific hosts (typically
for one-time or occasional needs like a model mirror); `on_premise` mode is intended for a
standing deployment integrated into a broader internal network, with correspondingly more
network reachability, still bounded by "the organization's own network" as a hard ceiling
(never public internet) — this distinction should be made explicit in deployment
documentation so an operator doesn't mistake `on_premise`'s broader reachability for reduced
sovereignty guarantees regarding the public internet specifically.
