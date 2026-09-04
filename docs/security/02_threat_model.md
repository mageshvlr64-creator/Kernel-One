# Threat Model (Consolidated)

> One-row-per-threat summary. Each threat's full detail lives in its own file
> (`05_prompt_injection.md` etc.); this file is the index and severity ranking.

| Threat | File | Severity if realized | Primary mitigation |
|---|---|---|---|
| Prompt Injection | `05_prompt_injection.md` | High | Untrusted-context boundary in agent kernel |
| Data Exfiltration | `06_data_exfiltration.md` | Critical | Network egress denial (REQ-NET-001) |
| Tool Abuse | `07_tool_abuse.md` | High | Per-call authorization, no chained privilege |
| Sandbox Escape | `08_sandbox_escape.md` | Critical | Container isolation (DEC-005) |
| Path Traversal | `09_path_traversal.md` | High | Canonical path resolution + boundary check |
| Privilege Escalation | `10_privilege_escalation.md` | Critical | Server-side role/clearance only |
| RAG Authorization Bypass | `11_rag_authorization_bypass.md` | High | Pre-ranking classification filter |
| Model Data Leakage | `12_model_data_leakage.md` | High | Scoped memory, no cross-workspace batching |
| Secret Exposure | `13_secret_exposure.md` | Critical | Redaction at logging/response layer |
| Network Sovereignty Bypass | `14_network_bypass.md` | Critical | OS/container-layer enforcement |
| Approval Bypass | `15_approval_bypass.md` | High | Execution-time approval check + re-approval rule |
| Audit Tampering | `16_audit_tampering.md` | Critical | DB-level append-only grant + hash chain |
| Malicious Documents | `17_malicious_documents.md` | Medium | Server-side type detection, size caps, patched parsers |
| Malicious Code | `18_malicious_code.md` | High | Hard resource limits at container layer |
| Denial of Service | `19_denial_of_service.md` | Medium | Rate limiting, bounded agent step/replan counts |
| Dependency Security | `20_dependency_security.md` | Medium | CI dependency scanning, pinned images |
| Container Security | `21_container_security.md` | High | Non-root, minimal capabilities, scoped mounts |
| Supply Chain Security | `22_supply_chain_security.md` | High | Checksum-verified checkpoints, pinned lockfiles |
| Data at Rest | `23_data_at_rest.md` | High | Disk encryption (deployment-level control) |
| Data in Transit | `24_data_in_transit.md` | Medium | TLS for multi-host deployments |

## Severity definitions

**Critical:** could result in classified data leaving the deployment boundary, or full
compromise of the audit trail's integrity. **High:** could result in unauthorized access
within the deployment, or a documented invariant (REQ-SEC-*) being violated without external
data loss. **Medium:** availability or defense-in-depth degradation without a direct
confidentiality/integrity breach.
