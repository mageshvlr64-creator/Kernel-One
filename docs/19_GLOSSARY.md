# Glossary

> Canonical definitions. Every other document uses these terms exactly as defined here — no
> synonyms (e.g. never "user request" when "Task" is meant).

| Term | Definition |
|---|---|
| **Agent** | The autonomous reasoning loop implemented by the Agent Kernel (`features/04_agent_kernel/`) that plans, executes, and verifies a Task. Not a separate process — a role the backend plays while processing a Task. |
| **Agent Kernel** | The component that turns a natural-language Task into a Plan of ToolInvocations and drives execution to completion. |
| **AgentRun** | One planning+execution attempt for a Task; a replan creates a new AgentRun (`domain/09_agent_model.md`). |
| **Air-gapped** | Network mode with zero outbound connectivity at all, including no DNS resolution (`reference/... network modes`, REQ-NET-002). |
| **Artifact** | A generated downloadable file (DOCX/PPTX/XLSX/PDF/CSV/JSON/Markdown/code) produced from Task output (`domain/14_artifact_model.md`). |
| **Asset** | An Equipment row (or its parent Plant/Unit) — a physical thing tracked with its own maintenance/inspection/incident history and governing documents, distinct from any single document that mentions it (`domain/20_asset_model.md`, `industrial/13_asset_knowledge_graph.md`). |
| **Audit Event** | An immutable, append-only record of one action taken by the system (`schemas/15_audit_event_schema.md`). |
| **Approval** | A human decision gate on a high-risk action (`domain/15_approval_model.md`). |
| **Classification** | The sensitivity label (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED) attached to Documents and propagated to derived entities (`reference/04_data_classification_levels.md`). |
| **Evidence** | A record linking a specific claim in agent output to a specific source passage (`domain/13_evidence_model.md`). |
| **Citation** | The rendered, user-visible form of an Evidence link attached to a text span. |
| **Claim** | A single factual assertion made in agent output; every Claim must have a backing Evidence row before it may be shown (`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`) — see Evidence, Verification. |
| **Inference Gateway** | The component normalizing calls to vLLM/Ollama/llama.cpp behind one interface (`features/03_inference_gateway/`). |
| **MoE (Mixture of Experts)** | A model architecture where only a subset of parameters ("active parameters") are used per token, but the full parameter set ("total parameters") must still be stored/loaded — see REQ-AI-003; never confuse the two when sizing hardware. |
| **Model Router** | The component that selects which Model handles a given request based on capability, policy, and resource fit (`features/02_model_router/`). |
| **Network Sovereignty** | The property, enforced and continuously verified, that no data leaves the deployment's own infrastructure (`features/18_network_sovereignty/`, REQ-NET-001..003). |
| **On-premise** | Network mode permitting outbound traffic only within the organization's own network, never the public internet (REQ-NET-002). |
| **Plan** | The ordered list of PlanSteps (tool invocations) an AgentRun intends to execute (`schemas/04_execution_schema.md`). |
| **Policy** | An operator-configured rule further restricting (never expanding) the base permission matrix (`domain/16_policy_model.md`). |
| **Provenance** | The full chain from a generated Artifact or claim back to its originating Document(s) — see Evidence. |
| **Quantization** | Reducing a model's numeric precision (e.g. FP16 → 4-bit) to shrink memory footprint at some accuracy cost (`07_HARDWARE_AND_DEPLOYMENT_CONSTRAINTS.md`). |
| **RAG (Retrieval-Augmented Generation)** | Answering by retrieving relevant DocumentChunks and grounding generation in them, rather than relying on the model's parametric memory alone (`features/13_knowledge_fabric/`). |
| **RBAC (Role-Based Access Control)** | The fixed six-role permission model (`reference/05_permission_matrix.md`). |
| **Reranking** | The second-stage relevance scoring applied to initial retrieval results before the top results are used as Evidence (`features/13_knowledge_fabric/10_reranking.md`) — the source of Evidence's raw `confidence` ranking signal (`domain/13_evidence_model.md`). |
| **Restricted (network mode)** | Network mode permitting outbound traffic only to an explicit operator-configured allowlist (REQ-NET-002). |
| **Revision** | A dated, superseding version of a Document distinct from its `version` counter — tracked via `Document.effective_from`/`effective_until`/`superseded_by` (`domain/06_document_model.md`), compared by `industrial/05_document_comparison.md` and `06_change_detection.md`. |
| **Sandbox** | The isolated container environment in which agent/model-generated code executes (`features/09_code_execution/`). |
| **Task** | One user-initiated unit of work processed by the Agent Kernel, with its own state machine (`domain/11_task_model.md`). |
| **Tool** | A registered capability (filesystem, calculator, database, code execution, etc.) an agent may invoke, subject to permission/classification checks (`domain/10_tool_model.md`). |
| **ToolInvocation** | One specific call to a Tool within a Task's execution, with its own state machine. |
| **Verification** | The post-generation pipeline stage that checks a Claim's citation validity, evidence support, and cross-source agreement before the Claim is shown as final (`features/14_evidence_and_provenance/09_unsupported_claim_detection.md`, `05_ARCHITECTURAL_PRINCIPLES.md` principle 4). |
| **Workspace** | The scoping boundary for Tasks, Documents, and Artifacts within an Organization (`domain/02_workspace_model.md`). |

## Rule

If a document needs a term not listed here, it is added here in the same change — a document
never introduces new terminology silently.
