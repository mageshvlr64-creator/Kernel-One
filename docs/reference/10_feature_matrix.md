# Feature Matrix (Reference)

> Master feature matrix per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §28 and §57 —
> one row per capability, using the 5-tier priority vocabulary (CORE MVP / V1 / V1.5 / FUTURE /
> RESEARCH) and the 6 columns §57 specifies. Supersedes the earlier 3-value
> (V1-committed/V1-aspirational/V2), coarser-grouped version of this table.

| Capability | Priority | MVP | Industrial value | Security impact | Demo |
|---|---|---|---|---|---|
| Model Management, Model Router, Inference Gateway (01-03) | CORE MVP | Yes | Indirect — underlies every workflow | Model trust/routing decisions | Implicit in every demo |
| Agent Kernel (04) | CORE MVP | Yes | Indirect — orchestrates all workflows | Bounded execution, replanning | Implicit in every demo |
| Tool Gateway, Filesystem/Calculator/Database/Code Execution tools (05-09) | CORE MVP | Yes | Deterministic calculations (industrial/10-11) run through here | Sandboxing, least privilege | Demo 5 (calculations) |
| Document Ingestion, OCR, Multimodal (10-12) | CORE MVP | Yes | Every industrial document type flows through here | Malicious document handling | Implicit in every demo |
| Knowledge Fabric (13) | CORE MVP | Yes | Hybrid retrieval underlies asset/knowledge-graph queries | Permission filtering at retrieval time | Demo 1 |
| Evidence and Provenance (14) | CORE MVP | Yes | Confidence methodology, knowledge trust fields | Prevents unsupported claims | Demo 1 |
| Artifact Engine (15) | CORE MVP | Yes | Report generation (`workflows/07_report_generation.md`) | Classification inheritance on export | Demo 5 |
| Human Approval (16) | CORE MVP | Yes | Conflict resolution requires this gate | Human-in-the-loop for high-risk actions | Demo 7 |
| Audit (17) | CORE MVP | Yes | Every asset/conflict edit is audited | Hash-chain integrity | Demo 7, Demo 8 |
| Network Sovereignty (18) | CORE MVP | Yes | — | Runtime attestation | Demo 8 |
| Identity and RBAC (19) | CORE MVP | Yes | Gates asset/document edit actions | Least privilege | Demo 6 |
| Data Classification (20) | CORE MVP | Yes | Classification on asset-linked documents | Never-decreases propagation | Demo 6 |
| Policy Engine (21) | CORE MVP | Yes | — | Centralized rule evaluation | Demo 6 |
| Agent Memory (22) | V1 (basic scope) | Yes, reduced scope | — | — | Not separately demoed |
| Spreadsheet Intelligence (23) | V1 | Yes | Supporting workflow, not primary demo path | — | Not a flagship demo |
| Admin Console, Observability, Backup/Recovery (24-26) | V1 | Yes | Operational necessity, not a differentiator | Operational integrity | Not separately demoed |
| Asset/Equipment domain model (`domain/20_asset_model.md`) | CORE MVP | Yes | The foundation of the whole industrial story | Governs asset-scoped classification | Demo 4 |
| Asset-Centric Knowledge Graph (`industrial/13`) | CORE MVP | Yes | Direct differentiator | Provenance-backed relationships only | Demo 4 |
| Document Revision Comparison (`industrial/05-06`) | CORE MVP | Yes | Flagship Workflow B | — | Demo 2 |
| Knowledge Conflict Detection (`industrial/14`) | CORE MVP | Yes | Flagship differentiator | Never-silent-resolution principle | Demo 3 |
| Inspection Report / Maintenance Record Intelligence (`industrial/02-04`) | CORE MVP | Yes | Flagship Workflow A | — | Demo 5 |
| Engineering Calculations (`industrial/10-11`) | CORE MVP | Yes | Flagship Workflow C | Deterministic verification | Demo 5 |
| P&ID / drawing intelligence (`industrial/08-09`) | V1.5 | No | Aspirational industrial capability | — | Explicitly caveated if shown |
| Coding agent, general spreadsheet chat | V1 | Yes (supporting) | None — explicitly demoted per §27 | — | Appendix, not a flagship demo |
| DLP (input-side scanning) | FUTURE | No | — | Currently a documented gap, see DEC-021 | Not demoed |
| Voice (speech/TTS) | FUTURE | No | None | — | Not demoed |
| Multi-node, Kubernetes | FUTURE | No | None | — | Not demoed |
| Enterprise identity (Keycloak) | FUTURE | No | None | — | Not demoed |
| Corpus-wide proactive conflict scanning | RESEARCH | No | Would extend `industrial/14` | — | Not demoed |

## Rule

A feature's status here must match its own file's scope statement — this table is a summary,
not an independent source of truth (the feature's own directory is authoritative).
