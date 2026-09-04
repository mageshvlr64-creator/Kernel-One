# Single-Server Deployment

> The bare-metal/VM equivalent of `03_docker_compose.md`, for operators who prefer not to run
> a container orchestrator distinct from Docker itself.

## Difference from `03_docker_compose.md`

None at the architecture level — `architecture/15_single_node_architecture.md` IS this
deployment; this file exists to state explicitly that "single server" and "Docker Compose
single-node" are the same target, not two different architectures, to avoid an operator
assuming a heavier orchestrator (Kubernetes) is required for a single-server deployment.

## Hardware mapping

Directly maps to PROFILE-B (demo-committed) or PROFILE-C (production single-node) from
`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` depending on the server's specs.
