# Dependency Graph

> Canonical component dependency graph: `component → dependency → reason`. Build order
> (`09_BUILD_ORDER.md`) is derived from this graph — a component is never scheduled before
> every dependency in its row.

| Component | Depends on | Reason |
|---|---|---|
| Identity Service (`19_identity_and_rbac`) | Database | Users/roles are the first thing every other check needs |
| Policy Engine (`21_policy_engine`) | Identity Service | Evaluates role + classification + workspace conditions |
| Audit Service (`17_audit`) | Database | Append-only event store; nothing else can safely mutate state before this exists |
| Model Router (`02_model_router`) | Model Management (`01_model_management`), Inference Gateway (`03_inference_gateway`), Policy Engine | Needs to know what models exist, how to reach them, and whether they're approved |
| Inference Gateway (`03_inference_gateway`) | Model Management, integrations (vLLM/Ollama/llama.cpp) | Adapts to whichever runtime actually hosts a model |
| Tool Gateway (`05_tool_gateway`) | Identity Service, Policy Engine, Audit Service | Every tool call must be authorized and logged before it runs |
| Filesystem/Calculator/Database/Code-Execution Tools | Tool Gateway | Registered tools invoked only through the gateway, never directly |
| Agent Kernel (`04_agent_kernel`) | Model Router, Tool Gateway, Human Approval (`16_human_approval`), Agent Memory (`22_agent_memory`) | Plans need a model, executes via tools, pauses on high-risk actions, and needs context across turns |
| Document Ingestion (`10_document_ingestion`) | Object Storage, Database | Stores originals and metadata before any processing |
| OCR (`11_ocr`) | Document Ingestion | Only invoked for pages Document Ingestion has already routed to it |
| Multimodal (`12_multimodal`) | Inference Gateway, Document Ingestion | Needs a vision-capable model and page-rendered images |
| Knowledge Fabric (`13_knowledge_fabric`) | Document Ingestion, pgvector (integration) | Chunks/embeds/indexes what ingestion produced |
| Evidence & Provenance (`14_evidence_and_provenance`) | Knowledge Fabric, Agent Kernel | Attaches retrieval results to specific claims in agent output |
| Artifact Engine (`15_artifact_engine`) | Evidence & Provenance, Task Model, Object Storage | Generated files must carry the same provenance as the answer they're based on |
| Human Approval (`16_human_approval`) | Identity Service, Policy Engine, Audit Service | Approval decisions are themselves permission- and audit-relevant actions |
| Network Sovereignty Monitor (`18_network_sovereignty`) | Audit Service | Blocked-attempt events must be auditable |
| Data Classification (`20_data_classification`) | Policy Engine | Classification checks are a specific instance of policy evaluation |
| Spreadsheet Intelligence (`23_spreadsheet_intelligence`) | Document Ingestion, Calculator Tool | Parses workbooks, then reasons over cells/formulas |
| Admin Console (`24_admin_console`) | Identity Service, Observability (`25_observability`) | Needs auth and health data to render |
| Observability (`25_observability`) | (no internal dependency — instruments everything else) | Cross-cutting; every other component depends on it, not the reverse |
| Backup/Recovery (`26_backup_recovery`) | Database, Object Storage | Backs up what those two components own |

## Build-order-relevant chains (see `09_BUILD_ORDER.md`)

```
Database → Identity Service → Policy Engine → Audit Service
                                     │
Model Management → Inference Gateway → Model Router ──┐
                                                        │
Tool Gateway ← Policy Engine, Audit Service ───────────┼──► Agent Kernel
                                                        │
Document Ingestion → OCR / Multimodal → Knowledge Fabric → Evidence & Provenance → Artifact Engine
                                                        │
                                          Human Approval ┘
```

## Rule

No component is implemented before every entry in its "Depends on" column exists at least in
stub form satisfying its own API contract (`docs/api/`) — a stub that returns `501` is
acceptable during early build phases; a component silently working around a missing
dependency is not.
