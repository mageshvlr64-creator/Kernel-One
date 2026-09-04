# Deployment Architecture

> The physical topology options, expanding on `deployment/` with the architectural reasoning
> behind each.

## V1 topology (single-node)

All services on one host (`architecture/15_single_node_architecture.md`), containers
networked via a single internal Docker bridge network with no route to the host's external
network interface for any container except the reverse proxy fronting the API/UI (and even
that is only bound to `localhost` or the internal LAN in `on_premise` mode, never a public
interface, per REQ-NET-001/002).

## Why containers even in single-node

Containerization isn't for scaling in V1 — it's for **isolation** (each service, especially
the sandbox, gets its own resource limits and network policy) and for **reproducibility**
(the exact same image runs in dev, demo, and any future multi-node deployment).

## Future topologies

`15_single_node_architecture.md` (V1), `16_multi_node_architecture.md` (V2, REQ-DEP-004
decision pending), `17_air_gapped_architecture.md`, `18_restricted_network_architecture.md`,
`19_on_premise_architecture.md` (network-mode-specific variants, orthogonal to node count).
