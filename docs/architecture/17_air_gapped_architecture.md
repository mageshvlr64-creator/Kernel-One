# Air-Gapped Architecture

> The `NETWORK_MODE=air_gapped` realization of `11_network_boundaries.md`.

## Defining property

Zero outbound connectivity, including no DNS resolution for any non-`localhost`/internal
address — this is the strictest of the three modes (REQ-NET-002) and is the mode used for the
reference demo (`demo/01_demo_overview.md`).

## Operational implication

All models, embedding models, and OCR engines must be pre-loaded onto the host **before** the
network is physically disconnected — there is no runtime model-download capability in this
mode, by design (a "download on demand" feature would itself require exactly the network
access this mode forbids).

## Verification

`features/18_network_sovereignty/`'s monitor continuously probes and confirms zero external
connectivity throughout operation — this is the mode `TEST-NET-001`/`SEC-TEST-008` are
specifically written against.
