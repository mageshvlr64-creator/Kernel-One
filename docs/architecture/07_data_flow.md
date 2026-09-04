# Data Flow

> How data moves through the system for the two primary flows: document ingestion and task
> execution. Complements `08_control_flow.md` (which covers control/authorization flow).

## Document data flow

```
Upload (UI) -> API -> Document Ingestion (writes Document row, uploads to Object Storage)
  -> OCR (if scanned) -> Knowledge Fabric (chunks, embeds, writes DocumentChunk rows)
  -> classification filter applied at every subsequent read, never only at write time
```

## Task data flow

```
User message (UI) -> API -> Agent Kernel (writes Task, AgentRun)
  -> Tool Gateway (writes ToolInvocation) <-> Tools (read/write their own domain, e.g.
     Filesystem Tool reads/writes the task workspace, Database Tool reads the target DB)
  -> Knowledge Fabric (read-only, for retrieval) -> Evidence & Provenance (writes Evidence)
  -> Artifact Engine (writes Artifact, reads Evidence for provenance)
  -> back to UI via the streaming execution API
```

## Cross-cutting data flow

Every write above also flows to the Audit Service (writes AuditEvent) in the same transaction
— this is not a separate "audit data flow" diagram because it's not optional or asynchronous;
it's part of every flow above by construction (REQ-AUD-001).
