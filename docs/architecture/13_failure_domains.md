# Failure Domains

> Which components' failures are isolated from which others — the architectural basis for
> `failures/44_partial_failure_recovery.md`'s "nothing left ambiguous" guarantee.

## Domains (V1, single-node)

| Failure domain | Isolated from | Shared fate with |
|---|---|---|
| Code Execution sandbox | Everything else — a sandbox crash/resource-exhaustion never affects the host or other tasks | Only the specific ToolInvocation/Task that triggered it |
| Inference Gateway (per provider) | Other providers — if vLLM crashes, Ollama/llama.cpp-backed capability slots are unaffected | Any Task/request specifically routed to the failed provider's models |
| Document Ingestion pipeline (per document) | Other documents — one document's OCR crash doesn't affect concurrent ingestion of others | Only that document's own state machine progress |
| Database | Nothing — a database failure is a shared-fate event across nearly every component, since most components depend on it (`10_DEPENDENCY_GRAPH.md`) | Everything except the UI's ability to show a cached error state |

## Why the database is a deliberately accepted single point of failure in V1

Per DEC-001/DEC-002, V1 is single-node with a single PostgreSQL instance — this is a conscious
tradeoff (simplicity over availability) documented here rather than hidden; V2 multi-node work
(`later/08_multi_node_scaling.md`) would introduce database replication specifically to
address this failure domain.
