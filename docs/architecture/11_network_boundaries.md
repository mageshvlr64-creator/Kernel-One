# Network Boundaries

> The network-layer realization of the trust and privilege boundaries above, and the direct
> architectural backing for REQ-NET-001/002.

## Boundaries by network mode

| Mode | Boundary |
|---|---|
| `air_gapped` | No route out of the deployment's own container network at all — not even DNS resolution succeeds for a non-`localhost`/internal address. |
| `restricted` | Route out permitted only to hosts explicitly listed in `RESTRICTED_MODE_ALLOWLIST` (`16_ENVIRONMENT_AND_CONFIGURATION.md`); everything else blocked identically to `air_gapped`. |
| `on_premise` | Route out permitted within the organization's own network (e.g. an internal package mirror, an internal LDAP server if `later/10_enterprise_identity_integration.md` is ever built) but never to the public internet. |

## Internal network segmentation (all modes)

The Code Execution sandbox has its own network boundary *inside* the deployment — even in
`on_premise` mode where other internal services might reach the organization's LAN, the
sandbox container specifically gets `--network=none` (DEC-005) regardless of the deployment's
overall network mode, since REQ-SEC-002 is independent of REQ-NET-002's mode selection.

## Enforcement layer

Enforced at the container/OS network layer (iptables/network namespaces), not application
code — see `security/14_network_bypass.md` for why this layering matters.
