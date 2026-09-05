# Threat Model (Consolidated)

> One-row-per-threat summary. Each threat's full detail lives in its own file
> (`05_prompt_injection.md` etc.); this file is the index and severity ranking.

| Threat | File | Severity if realized | Likelihood | Primary mitigation | Residual risk | Test |
|---|---|---|---|---|---|---|
| Prompt Injection | `05_prompt_injection.md` | High | High — any ingested document/tool output is a potential vector | Untrusted-context boundary in agent kernel | Novel injection techniques not yet seen | SEC-TEST-005 |
| Data Exfiltration | `06_data_exfiltration.md` | Critical | Low, given network egress denial | Network egress denial (REQ-NET-001) | Covert channel via timing/side-channel (not addressed in V1) | SEC-TEST-006 |
| Tool Abuse | `07_tool_abuse.md` | High | Medium | Per-call authorization, no chained privilege | A permitted tool used for an unintended but technically-allowed purpose | SEC-TEST-007 |
| Sandbox Escape | `08_sandbox_escape.md` | Critical | Low | Container isolation (DEC-005) | Undiscovered container-runtime vulnerability | SEC-TEST-008 |
| Path Traversal | `09_path_traversal.md` | High | Medium | Canonical path resolution + boundary check | Symlink-based bypass not yet tested | SEC-TEST-009 |
| Privilege Escalation | `10_privilege_escalation.md` | Critical | Low | Server-side role/clearance only | Logic error in policy engine evaluation | SEC-TEST-010 |
| RAG Authorization Bypass | `11_rag_authorization_bypass.md` | High | Medium | Pre-ranking classification filter | Reranker exposing snippet text before the filter runs | SEC-TEST-011 |
| Model Data Leakage | `12_model_data_leakage.md` | High | Low | Scoped memory, no cross-workspace batching | Fine-tuning/caching layer not covered by this scope | SEC-TEST-012 |
| Secret Exposure | `13_secret_exposure.md` | Critical | Medium — no input-side DLP in V1 (DEC-021) | Redaction at logging/response layer | A secret embedded mid-document, never logged but retrieved and displayed verbatim | SEC-TEST-013 |
| Network Sovereignty Bypass | `14_network_bypass.md` | Critical | Low | OS/container-layer enforcement | Misconfigured deployment overriding the network policy | SEC-TEST-014 |
| Approval Bypass | `15_approval_bypass.md` | High | Low | Execution-time approval check + re-approval rule | Race condition between approval and execution (not yet load-tested) | SEC-TEST-015 |
| Audit Tampering | `16_audit_tampering.md` | Critical | Low | DB-level append-only grant + hash chain | Compromised DB superuser account | SEC-TEST-016 |
| Malicious Documents | `17_malicious_documents.md` | Medium | High — every ingested file is untrusted input | Server-side type detection, size caps, patched parsers | Zero-day in a parsing library | SEC-TEST-017 |
| Malicious Code | `18_malicious_code.md` | High | Medium | Hard resource limits at container layer | Resource-exhaustion within the allowed limits | SEC-TEST-018 |
| Denial of Service | `19_denial_of_service.md` | Medium | Medium | Rate limiting, bounded agent step/replan counts | Distributed request pattern within per-client limits | SEC-TEST-019 |
| Dependency Security | `20_dependency_security.md` | Medium | Medium | CI dependency scanning, pinned images | Zero-day in a pinned dependency before a patch exists | SEC-TEST-020 |
| Container Security | `21_container_security.md` | High | Low | Non-root, minimal capabilities, scoped mounts | Kernel-level container-escape vulnerability | SEC-TEST-021 |
| Supply Chain Security | `22_supply_chain_security.md` | High | Low | Checksum-verified checkpoints, pinned lockfiles | Compromised upstream package before detection | SEC-TEST-022 |
| Data at Rest | `23_data_at_rest.md` | High | Low | Disk encryption (deployment-level control) | Operator fails to enable disk encryption (deployment misconfiguration, not a code defect) | SEC-TEST-023 |
| Data in Transit | `24_data_in_transit.md` | Medium | Low | TLS for multi-host deployments | Single-node deployments with no inter-service TLS (accepted for single-node, see `architecture/15_single_node_architecture.md`) | SEC-TEST-024 |
| Compromised Local User | *(new — no per-threat detail file yet, tracked in DEC-021)* | High | Medium | RBAC least-privilege limits blast radius of one compromised account | An insider or phished operator account is used within its legitimate permissions | Not yet in `reference/13_test_matrix.md` |
| Unauthorized Model Access | *(new — no per-threat detail file yet, tracked in DEC-021)* | Medium | Low | Model access gated by the same RBAC/policy checks as any other Tool | A misconfigured deployment exposing the inference gateway port directly | Not yet in `reference/13_test_matrix.md` |
| Malicious Generated Artifacts | *(new — no per-threat detail file yet, tracked in DEC-021)* | Medium | Low | Artifact classification inheritance + approval gate before export | A generated document embedding executable content that itself becomes a delivery vector | Not yet in `reference/13_test_matrix.md` |
| Poisoned Knowledge | *(new — no per-threat detail file yet, tracked in DEC-021)* | High | Medium | `Document.authority`/`effective_from` fields and `industrial/14_knowledge_conflict_detection.md` surface disagreement rather than silently trusting new content | A single ingested document deliberately crafted to outrank a correct one in retrieval, with no independent authority check yet automated beyond the fields above | Not yet in `reference/13_test_matrix.md` |
| Stale Documents | *(new — no per-threat detail file yet, tracked in DEC-021)* | Medium | Medium — retrieval-time temporal filtering not yet wired in (`domain/06_document_model.md`) | `effective_from`/`effective_until` fields exist; enforcement in the default retrieval path is a tracked gap | An undated query silently serving a since-superseded document as if current | Not yet in `reference/13_test_matrix.md` |

## Severity definitions

**Critical:** could result in classified data leaving the deployment boundary, or full
compromise of the audit trail's integrity. **High:** could result in unauthorized access
within the deployment, or a documented invariant (REQ-SEC-*) being violated without external
data loss. **Medium:** availability or defense-in-depth degradation without a direct
confidentiality/integrity breach.
