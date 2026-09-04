# Service Boundaries

> The physical (process/container) realization of `05_component_boundaries.md`, matching
> `15_CODEBASE_TARGET_STRUCTURE.md`'s `services/` directory 1:1.

## Rule

Every entry in `05_component_boundaries.md`'s ownership table corresponds to exactly one
service under `services/` in the codebase structure — there is no entity owned by "part of"
a service or split across two services.

## Cross-service calls

A service needing data owned by another service calls that service's API (internal HTTP or,
in V1, a direct in-process function call if co-located — but never a direct database query
against another service's tables, even when both happen to share the same PostgreSQL
instance in V1's single-node deployment). This discipline is what makes
`16_multi_node_architecture.md` a configuration change later, not a rewrite.

## Enforcement

`15_CODEBASE_TARGET_STRUCTURE.md`'s dependency direction rule (`services/*` never imports
another `services/*` directly) is the code-level enforcement of this boundary — a lint rule
checking cross-service imports is part of `08_BUILD_PHASES.md` Phase 0 tooling.
