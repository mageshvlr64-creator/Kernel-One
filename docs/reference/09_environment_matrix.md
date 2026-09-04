# Environment Matrix (Reference)

> Cross-reference of deployment profile × network mode × expected use, consolidating
> `07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md` and `deployment/`.

| Profile | Typical network mode | Typical use | Deployment file |
|---|---|---|---|
| PROFILE-A | `restricted` (setup) → `air_gapped` (testing) | Development | `deployment/02_local_development.md` |
| PROFILE-B | `air_gapped` | Demo / pilot | `deployment/03_docker_compose.md`, `06_cpu_only_demo.md` |
| PROFILE-C | `air_gapped` / `restricted` / `on_premise` | Single-node production | `deployment/04_single_server.md`, `07..09_*_deployment.md` |
| PROFILE-D | `air_gapped` / `restricted` / `on_premise` | Larger enterprise (V2 multi-node likely needed, `later/08_multi_node_scaling.md`) | Same as PROFILE-C plus future multi-node files |

## Rule

Every combination in this table is a valid, named target — a deployment should be describable
as "PROFILE-X in MODE-Y" unambiguously, per this matrix.
