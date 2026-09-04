# Restricted Network Architecture

> The `NETWORK_MODE=restricted` realization of `11_network_boundaries.md`.

## Defining property

Outbound connectivity permitted only to hosts explicitly listed in
`RESTRICTED_MODE_ALLOWLIST` (`16_ENVIRONMENT_AND_CONFIGURATION.md`) — e.g. an internal model
mirror registry the organization runs, still within its own network, never the public
internet.

## Use case

Useful during initial setup (pulling model weights/dependencies from an internal mirror) or
for organizations that need occasional, tightly-controlled connectivity (e.g. periodic
internal registry sync) without full air-gap operation.

## Verification

The same network monitor (`features/18_network_sovereignty/`) confirms that only allowlisted
hosts are reachable and everything else remains blocked — `restricted` mode is not "network
sovereignty off," it's "network sovereignty with one named, audited exception list."
