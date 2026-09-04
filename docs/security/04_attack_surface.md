# Attack Surface

> Enumerated entry points, cross-referenced to the threat(s) each one is most relevant to.

| Entry point | Exposed to | Primary relevant threats |
|---|---|---|
| `POST /api/v1/auth/login` | Network (internal only in air_gapped/on_premise) | Privilege Escalation, Denial of Service |
| Document upload (`api/11_documents_api.md`) | Authenticated users | Malicious Documents, RAG Authorization Bypass |
| Chat/Task input (`api/05_chat_api.md`, `06_tasks_api.md`) | Authenticated users | Prompt Injection, Denial of Service |
| Tool invocation (`api/15_tools_api.md`, `16_sandbox_api.md`) | Agent Kernel (primarily), directly callable by privileged roles | Tool Abuse, Sandbox Escape, Path Traversal, Data Exfiltration |
| Approval decision (`api/18_approval_api.md`) | Administrator/SecurityOfficer | Approval Bypass, Privilege Escalation |
| Admin/config endpoints (`api/23_admin_api.md`) | Administrator/Operator | Secret Exposure, Privilege Escalation |
| Model registry (`api/09_model_registry_api.md`) | Administrator/Operator | Supply Chain Security |
| Inter-service calls (internal) | Internal network only | Network Sovereignty Bypass (if a service attempts external egress) |
| Container base images / dependencies | Build pipeline, not runtime | Dependency Security, Supply Chain Security |

## Minimization principle

Any new API endpoint or tool added to the system must be added to this table in the same
change, with its relevant threats identified — an endpoint that isn't in this table has not
completed security review per `08_BUILD_PHASES.md` Phase 8 exit criteria.
