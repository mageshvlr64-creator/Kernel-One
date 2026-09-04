# State Machines (Canonical)

> **Canonical owner** of every entity state machine in the system. `runtime/04_agent_state_machine.md`
> through `runtime/09_artifact_state_machine.md` each hold the specific machine named in their
> title; this file is the index and the shared conventions all of them follow. No feature
> document defines its own state names — it references the relevant machine below.

## Shared conventions

- Every transition has an **owner** (the component allowed to trigger it), a **side effect**,
  a **required audit event**, and defined **error behavior** if attempted illegally.
- An illegal transition attempt (e.g. approving an already-rejected approval) returns
  `RESOURCE_CONFLICT` (`reference/01_error_codes.md`) and is itself an audit event.
- State names are `UPPER_SNAKE_CASE` and are identical across the domain model, the database
  schema, the API responses, and the UI — no synonyms.

## Task

| State | Entered from | Exit transitions | Owner | Side effect | Audit event |
|---|---|---|---|---|---|
| `CREATED` | (initial) | → `PLANNING` | Agent Kernel | Task row inserted | `task.created` |
| `PLANNING` | `CREATED`, `WAITING_INPUT` | → `WAITING_APPROVAL`, `EXECUTING`, `FAILED` | Agent Kernel | Plan generated and validated | `task.plan_generated` |
| `WAITING_APPROVAL` | `PLANNING` | → `EXECUTING` (approved), → `FAILED` (rejected), → `CANCELLED` (expired) | Human Approval | Approval request created | `task.approval_requested` |
| `EXECUTING` | `WAITING_APPROVAL`, `PLANNING` | → `WAITING_INPUT`, → `COMPLETED`, → `FAILED`, → `PLANNING` (replan) | Agent Kernel | Plan steps executed in order | `task.step_executed` (per step) |
| `WAITING_INPUT` | `EXECUTING` | → `PLANNING` (input received) | Agent Kernel | Task paused pending user reply | `task.waiting_input` |
| `COMPLETED` | `EXECUTING` | (terminal) | Agent Kernel | Final artifact/response attached | `task.completed` |
| `FAILED` | `PLANNING`, `WAITING_APPROVAL`, `EXECUTING` | (terminal) | Agent Kernel | Failure reason recorded | `task.failed` |
| `CANCELLED` | any non-terminal | (terminal) | User or Admin | Cancellation reason recorded | `task.cancelled` |

**Illegal transitions:** any transition not listed above (e.g. `COMPLETED` → `EXECUTING`)
returns `RESOURCE_CONFLICT`.

## ToolInvocation

| State | Entered from | Exit transitions | Owner | Side effect | Audit event |
|---|---|---|---|---|---|
| `CREATED` | (initial) | → `AUTHORIZED`, → `FAILED` (denied) | Tool Gateway | Invocation row inserted | `tool_invocation.created` |
| `AUTHORIZED` | `CREATED` | → `RUNNING` | Tool Gateway | Policy check passed | `tool_invocation.authorized` |
| `RUNNING` | `AUTHORIZED` | → `SUCCEEDED`, → `FAILED`, → `TIMEOUT`, → `CANCELLED` | Tool implementation | Tool executes | `tool_invocation.started` |
| `SUCCEEDED` | `RUNNING` | (terminal) | Tool implementation | Result stored | `tool_invocation.succeeded` |
| `FAILED` | `CREATED`, `RUNNING` | (terminal) | Tool Gateway / implementation | Error stored | `tool_invocation.failed` |
| `TIMEOUT` | `RUNNING` | (terminal) | Tool Gateway | Process/container killed | `tool_invocation.timeout` |
| `CANCELLED` | `AUTHORIZED`, `RUNNING` | (terminal) | User or Agent Kernel | Process/container killed | `tool_invocation.cancelled` |

## Approval

| State | Entered from | Exit transitions | Owner | Side effect | Audit event |
|---|---|---|---|---|---|
| `REQUESTED` | (initial) | → `APPROVED`, → `REJECTED`, → `EXPIRED`, → `CANCELLED` | Human Approval | Approval row inserted, UI notified | `approval.requested` |
| `APPROVED` | `REQUESTED` | (terminal — triggers dependent Task/ToolInvocation transition) | Administrator / Security Officer | Gated action unblocked | `approval.approved` |
| `REJECTED` | `REQUESTED` | (terminal) | Administrator / Security Officer | Gated action fails | `approval.rejected` |
| `EXPIRED` | `REQUESTED` | (terminal) | System (timer) | Gated action fails; default expiry: 24h — **CONFIG DEFAULT** | `approval.expired` |
| `CANCELLED` | `REQUESTED` | (terminal) | Requesting user | Gated action fails | `approval.cancelled` |

**Note:** editing the underlying action after `REQUESTED` invalidates the approval — it
transitions to `CANCELLED` and a new `REQUESTED` approval must be created (re-approval rule).

## Artifact

| State | Entered from | Exit transitions | Owner | Side effect | Audit event |
|---|---|---|---|---|---|
| `CREATED` | (initial) | → `VALIDATING` | Artifact Engine | File generation started | `artifact.created` |
| `VALIDATING` | `CREATED` | → `READY`, → `FAILED` | Artifact Engine | Structural validation (e.g. DOCX opens, XLSX parses) | `artifact.validated` |
| `READY` | `VALIDATING` | → `APPROVED` (if classification requires), → `EXPORTED` (if no approval required) | Artifact Engine | Available for download in-app | `artifact.ready` |
| `APPROVED` | `READY` | → `EXPORTED` | Administrator / Security Officer | Export unblocked | `artifact.approved` |
| `REJECTED` | `READY` | (terminal) | Administrator / Security Officer | Export blocked | `artifact.rejected` |
| `EXPORTED` | `READY`, `APPROVED` | (terminal, but see Deleted) | User | File delivered outside the workbench boundary (download) | `artifact.exported` |
| `DELETED` | any | (terminal) | User or retention policy | File removed from storage | `artifact.deleted` |
| `FAILED` | `VALIDATING` | (terminal) | Artifact Engine | Generation error recorded | `artifact.failed` |

## Document

| State | Entered from | Exit transitions | Owner | Side effect | Audit event |
|---|---|---|---|---|---|
| `UPLOADED` | (initial) | → `VALIDATING` | Document Ingestion | File stored in object storage, hash computed | `document.uploaded` |
| `VALIDATING` | `UPLOADED` | → `EXTRACTING`, → `FAILED` | Document Ingestion | File type/size/malware-signature checked | `document.validated` |
| `EXTRACTING` | `VALIDATING` | → `OCR` (if scanned), → `INDEXING` (if native text), → `FAILED` | Document Ingestion | Text/layout extraction | `document.extracted` |
| `OCR` | `EXTRACTING` | → `INDEXING`, → `FAILED` | OCR | Text recognized per page | `document.ocr_completed` |
| `INDEXING` | `EXTRACTING`, `OCR` | → `READY`, → `FAILED` | Knowledge Fabric | Chunked, embedded, indexed | `document.indexed` |
| `READY` | `INDEXING` | → `DELETED` | Document Ingestion | Searchable/retrievable | (none — terminal success state) |
| `FAILED` | `VALIDATING`, `EXTRACTING`, `OCR`, `INDEXING` | (terminal) | Document Ingestion | Failure reason recorded | `document.failed` |
| `DELETED` | `READY` | (terminal) | User or retention policy | File and derived chunks/embeddings removed | `document.deleted` |

## Machine-readable representation

Each machine above is additionally maintained as a state-table in
`schemas/18_agent_state_schema.md` (for Task/ToolInvocation) and the relevant entity schema
file, using the shape:

```json
{
  "entity": "Task",
  "states": ["CREATED", "PLANNING", "WAITING_APPROVAL", "EXECUTING", "WAITING_INPUT", "COMPLETED", "FAILED", "CANCELLED"],
  "transitions": [
    {"from": "CREATED", "to": "PLANNING", "owner": "agent_kernel", "audit_event": "task.created"}
  ]
}
```

This JSON form is what the runtime's transition-guard function validates against — the tables
above are the human-readable rendering of the same source data, not a separate definition.
