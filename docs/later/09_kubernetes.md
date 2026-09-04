# Kubernetes Deployment (V2+)

> A specific realization of `08_multi_node_scaling.md` using Kubernetes as the orchestrator,
> as opposed to the Docker Compose-based single-node deployment used for V1
> (`deployment/03_docker_compose.md`).

## Why not V1

`deployment/03_docker_compose.md` already meets PROFILE-B's single-node target with
substantially less operational complexity than a Kubernetes cluster — introducing Kubernetes
for a single-workstation demo would be disproportionate engineering cost with no V1 benefit,
consistent with the reasoning in `20_DECISION_LOG.md` DEC-001.

## What this would need when scheduled

- Helm charts (or equivalent) mirroring the service boundaries in
  `15_CODEBASE_TARGET_STRUCTURE.md`.
- A decision on whether GPU scheduling uses the Kubernetes device plugin model directly or a
  higher-level scheduler (e.g. for fractional GPU sharing across smaller models) —
  `DECISION REQUIRED` when this work begins.
- Network policy definitions that enforce the same `NETWORK_MODE` guarantees
  (`features/18_network_sovereignty/`) at the Kubernetes NetworkPolicy layer, not just the
  application layer — REQ-NET-001 must hold regardless of orchestrator.
