# Dependency Matrix (Reference)

> Restates `10_DEPENDENCY_GRAPH.md` as a flat lookup table (component → direct dependencies
> only, no transitive chains) for quick reference.

| Component | Direct dependencies |
|---|---|
| Identity Service | Database |
| Policy Engine | Identity Service |
| Audit Service | Database |
| Model Management | Database |
| Inference Gateway | Model Management, vLLM/Ollama/llama.cpp |
| Model Router | Model Management, Inference Gateway, Policy Engine |
| Tool Gateway | Identity Service, Policy Engine, Audit Service |
| Filesystem/Calculator/Database/Code-Execution Tools | Tool Gateway |
| Agent Kernel | Model Router, Tool Gateway, Human Approval, Agent Memory |
| Document Ingestion | Object Storage, Database |
| OCR | Document Ingestion |
| Multimodal | Inference Gateway, Document Ingestion |
| Knowledge Fabric | Document Ingestion, pgvector |
| Evidence & Provenance | Knowledge Fabric, Agent Kernel |
| Artifact Engine | Evidence & Provenance, Object Storage |
| Human Approval | Identity Service, Policy Engine, Audit Service |
| Network Sovereignty Monitor | Audit Service |
| Data Classification | Policy Engine |
| Spreadsheet Intelligence | Document Ingestion, Calculator Tool |
| Admin Console | Identity Service, Observability |
| Observability | (none — cross-cutting) |
| Backup/Recovery | Database, Object Storage |

## Full reasoning

See `10_DEPENDENCY_GRAPH.md` for the "reason" column explaining *why* each dependency exists —
this file is the flat lookup only.
