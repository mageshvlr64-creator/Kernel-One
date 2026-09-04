# Network Sovereignty Bypass

> Threat entry. Format follows `01_security_architecture.md`'s convention: threat description,
> where it can occur, mitigation, and traceability to requirements/tests.

## Threat

An attempt to reach an external host despite the active network mode — via DNS-over-HTTPS to bypass DNS-level blocking, a hardcoded IP literal, or a compromised dependency phoning home.

## Where it can occur

Any process with outbound capability; primarily Code Execution and Inference Gateway (if a provider library has unexpected telemetry).

## Mitigation

Enforcement happens at the OS/container network layer (iptables/network namespace/`--network=none`), not only DNS blocking — an IP-literal connection attempt is blocked identically to a DNS-resolved one (REQ-NET-001).

## Traceability

- Requirements: `REQ-NET-001`
- Tests: `SEC-TEST-008`

## Residual risk

Every mitigation above reduces but does not claim to eliminate risk to zero — where a
mitigation is preventive (e.g. container isolation), a detective control (audit logging) is
also in place so a successful bypass is still discoverable after the fact, per
`security/01_security_architecture.md`'s defense-in-depth principle.
