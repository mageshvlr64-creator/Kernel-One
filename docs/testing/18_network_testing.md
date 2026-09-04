# Network Testing

> Covers `features/18_network_sovereignty/` — the tests underpinning REQ-NET-001/002/003.

## Required tests

- `TEST-NET-001`: packet capture during a full demo session shows zero external DNS/TCP/HTTP
  connections (`security/02_threat_model.md`'s Network Sovereignty Bypass entry).
- `TEST-NET-002`: air-gapped mode specifically — no DNS resolution succeeds for any
  non-`localhost`/internal address.
- `TEST-NET-003`: switching `NETWORK_MODE` changes enforced behavior with no code change,
  verified across all three modes on the same built image.
- `SEC-TEST-008`: full system in `air_gapped` mode, automated harness attempts DNS/TCP
  connections from every component — all fail.
