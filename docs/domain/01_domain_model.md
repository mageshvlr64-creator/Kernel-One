# Domain Model (Index)

> **Canonical owner** of the entity-relationship overview. Each entity's field-level detail
> lives in its own file under `docs/domain/`, linked below. This file does not redefine fields
> already defined elsewhere.

## Entity list and owning file

| Entity | Defined in |
|---|---|
| Workspace | `02_workspace_model.md` |
| Organization | `03_organization_model.md` |
| User, Role | `04_user_model.md`, `05_identity_model.md` |
| Document, DocumentChunk | `06_document_model.md`, `07_knowledge_model.md` |
| Model, ModelDeployment, ModelCapability | `08_model_provider_model.md` |
| AgentRun | `09_agent_model.md` |
| Tool, ToolInvocation, TaskStep | `10_tool_model.md` |
| Task | `11_task_model.md` |
| Conversation, Message | `12_execution_model.md` |
| Evidence, Citation | `13_evidence_model.md` |
| Artifact | `14_artifact_model.md` |
| Approval | `15_approval_model.md` |
| Policy | `16_policy_model.md` |
| AuditEvent | `17_audit_event_model.md` (full schema in `schemas/15_audit_event_schema.md`) |
| MemoryEntry | `18_memory_model.md` |
| ClassificationLevel (enum, not a table) | `19_classification_model.md` |

## Relationship overview

```
Organization 1---* Workspace 1---* Document 1---* DocumentChunk
                       |                |
                       |                +--* Evidence *--1 Task
                       |
                       +--* User *--1 Role
                       |
                       +--* Task 1---1 Conversation 1---* Message
                             |
                             +--1 AgentRun (current) -- * ToolInvocation
                             +--* Evidence
                             +--* Artifact
                             +--* Approval
                             +--* AuditEvent (via correlation_id)

Model 1---* ModelCapability (inline array, not a join table in V1)
Policy independently referenced by AgentRun/ToolInvocation/Document/Artifact evaluation paths
  via the policy engine (features/21_policy_engine/) -- not a direct foreign key relationship.
```

## Cross-cutting rules that apply to every entity

1. **Classification propagation (REQ-DATA-001):** any entity derived from a classified
   Document (DocumentChunk, Evidence, Artifact) inherits the highest classification among its
   sources; it is never computed lower than any input.
2. **Audit on every mutation (REQ-AUD-001):** every insert/update/soft-delete on any table
   listed above produces exactly one `AuditEvent` in the same transaction.
3. **Soft delete, not hard delete, for anything with audit relevance:** `Document`, `User`,
   `Artifact`, `Workspace` use a `deleted_at` marker; `AuditEvent` rows are never deleted by
   application code at all (append-only, REQ-SEC-005). `DocumentChunk`, `MemoryEntry`, and
   `ToolInvocation` rows may be hard-deleted by retention jobs since they are derived/ephemeral,
   not primary records.
4. **No entity is queried without its classification/workspace filter applied at the database
   query level** (not filtered after the fact in application code) -- see
   `features/13_knowledge_fabric/12_permission_filtering.md` for the specific implementation
   this rule constrains.

## Machine-readable form

The exact column types, constraints, and indexes for every entity above are additionally
maintained in `docs/schemas/01_database_schema.md` as literal DDL -- this file is the
conceptual/relationship view; that file is the literal schema.
