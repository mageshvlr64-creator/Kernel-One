# Restricted Network Deployment

> Concrete deployment procedure for `NETWORK_MODE=restricted`
> (`architecture/18_restricted_network_architecture.md`).

## Procedure

1. Identify and document the exact hosts needed (e.g. `internal-model-mirror.corp:443`) —
   this list becomes `RESTRICTED_MODE_ALLOWLIST` (`16_ENVIRONMENT_AND_CONFIGURATION.md`).
2. Configure the host firewall/container network policy to allow only those hosts outbound,
   deny everything else — this is enforced at the same OS/container layer as `air_gapped`
   mode, just with a non-empty allowlist.
3. Set `NETWORK_MODE=restricted` with the allowlist populated, run `02_startup.md`.
4. Verify via the Network Sovereignty Panel that only allowlisted hosts show as reachable and
   everything else is blocked.

## Governance

Any addition to the allowlist is itself a change that should go through the same review
rigor as a Policy change (`domain/16_policy_model.md`) — an ungoverned, growing allowlist
erodes the meaningful difference between `restricted` and no restriction at all.
