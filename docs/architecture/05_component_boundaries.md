# Component Boundaries

> Where one component's responsibility ends and another's begins — the basis for
> `06_service_boundaries.md`'s physical realization.

## Rule

A component boundary is defined by **what state it exclusively owns**, not by what code
happens to call it. Per `domain/01_domain_model.md`'s ownership rule: exactly one component
writes to each table, every other component reads through that owner's API/internal interface.

## Boundary table (owner of each core entity)

| Entity | Sole writer |
|---|---|
| User, Role | Identity Service |
| Task, AgentRun | Agent Kernel |
| ToolInvocation | Tool Gateway |
| Document, DocumentChunk | Document Ingestion / Knowledge Fabric |
| Evidence | Evidence & Provenance service |
| Artifact | Artifact Engine |
| Approval | Human Approval service |
| Policy | Policy Engine (via Admin Console UI) |
| AuditEvent | Audit Service (all other services call its write API, never insert directly) |

## Consequence

No component's code directly executes `INSERT`/`UPDATE` SQL against a table it doesn't own —
even same-database access goes through the owning service's internal interface
(`domain/` "Ownership" section per entity), which is what keeps `10_DEPENDENCY_GRAPH.md`
accurate as code, not just as a diagram.
