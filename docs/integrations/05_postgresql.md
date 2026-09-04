# PostgreSQL Integration

> The single relational + vector database (DEC-002), not an "integration" in the optional
> sense — this is a hard dependency of nearly every service (`10_DEPENDENCY_GRAPH.md`).

## Version and extensions

PostgreSQL 15+, `pgvector` extension (see `06_pgvector.md`), `pgcrypto` for `gen_random_uuid()`.

## Connection pooling

Each service maintains its own connection pool (sized per
`performance/04_cpu_budgets.md`/`03_memory_budgets.md` budgets); no service holds a single
long-lived connection that would block concurrent requests.

## Health check

`SELECT 1` with a 2s timeout, per `deployment/13_health_checks.md`.
