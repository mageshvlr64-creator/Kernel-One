# Build Order

> Fine-grained implementation order within and across the phases in `08_BUILD_PHASES.md`,
> derived mechanically from `10_DEPENDENCY_GRAPH.md` — a component's number here is always
> higher than every component in its "Depends on" list.

| # | Component | Phase |
|---|---|---|
| 1 | Database schema + migrations | 0 |
| 2 | Configuration loader | 1 |
| 3 | Identity Service (`19_identity_and_rbac`) | 1 |
| 4 | Policy Engine (`21_policy_engine`) | 1 |
| 5 | Audit Service (`17_audit`) | 1 |
| 6 | Model Management (`01_model_management`) | 2 |
| 7 | Inference Gateway (`03_inference_gateway`) — one provider | 2 |
| 8 | Model Router (`02_model_router`) — single capability | 2 |
| 9 | Tool Gateway (`05_tool_gateway`) | 3 |
| 10 | Calculator Tool (`07_calculator_tool`) | 3 |
| 11 | Agent Kernel (`04_agent_kernel`) — plan/execute, no replanning | 3 |
| 12 | Filesystem Tool (`06_filesystem_tool`) | 4 |
| 13 | Code Execution / Sandbox (`09_code_execution`) | 4 |
| 14 | Document Ingestion (`10_document_ingestion`) | 5 |
| 15 | OCR (`11_ocr`) | 5 |
| 16 | Knowledge Fabric (`13_knowledge_fabric`) | 5 |
| 17 | Evidence & Provenance (`14_evidence_and_provenance`) | 6 |
| 18 | Human Approval (`16_human_approval`) | 7 |
| 19 | Artifact Engine (`15_artifact_engine`) | 7 |
| 20 | Data Classification (`20_data_classification`) — full enforcement | 8 |
| 21 | Network Sovereignty Monitor (`18_network_sovereignty`) | 8 |
| 22 | Multimodal (`12_multimodal`), Database Tool (`08_database_tool`), Spreadsheet Intelligence (`23_spreadsheet_intelligence`), Agent Memory (`22_agent_memory`) | 8 (parallel, no cross-dependency) |
| 23 | Observability (`25_observability`) | 9 |
| 24 | Admin Console (`24_admin_console`) | 9 |
| 25 | Backup/Recovery (`26_backup_recovery`) | 9 |
| 26 | Additional Inference Gateway providers (vLLM, Ollama) | 9 (parallel with 23-25) |
| 27 | Demo hardening, DEC-013/DEC-014 resolution | 10 |

## Parallelization note

Items at the same phase with no dependency edge between them (`10_DEPENDENCY_GRAPH.md`) may be
built in parallel by different engineers/agents — the numbering above is a valid *sequential*
order, not a claim that every earlier-numbered item strictly blocks every later one.
