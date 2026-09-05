# System Architecture

## High-level shape

The Sovereign AI Workbench is a single-tenant-per-deployment system composed of five layers, all of which
can run on one machine for V1 and can be split across machines for larger deployments
(`architecture/16_multi_node_architecture.md`):

1. **UI layer** — the workbench frontend (`ui/`).
2. **API layer** — the HTTP/WebSocket surface (`api/`) enforcing auth, RBAC, and policy before
   anything else runs.
3. **Agent kernel layer** — plans, schedules, and verifies task execution
   (`features/04_agent_kernel/`).
4. **Capability layer** — the model router and inference gateway
   (`features/02_model_router/`, `features/03_inference_gateway/`), the tool gateway and its
   individual tools (`features/05_tool_gateway/` through `features/09_code_execution/`), the
   knowledge fabric (`features/13_knowledge_fabric/`), and the artifact engine
   (`features/15_artifact_engine/`). Within this layer, two branches sit side by side rather
   than one being a thin skin on the other (per
   `SIH26117_Documentation_Refactor_Master_Prompt.txt` §5):
   - **Sovereign AI Core** — the generic agentic platform capabilities listed above: model
     routing, retrieval, tool execution, artifact generation. Reusable for any document/task
     type.
   - **Industrial Intelligence** — asset-centric capabilities built on top of the Core, not
     alongside it as an unrelated feature: the asset/equipment entity model
     (`domain/20_asset_model.md`), the asset-centric knowledge graph
     (`industrial/13_asset_knowledge_graph.md`), document revision comparison
     (`industrial/05_document_comparison.md`, `06_change_detection.md`), and cross-document
     knowledge conflict detection (`industrial/14_knowledge_conflict_detection.md`). This
     branch is what the product's positioning (`00_README.md`, `01_PRODUCT_VISION.md`) leads
     with — the Core exists to serve it, not the reverse.
5. **Trust layer** — identity/RBAC, policy engine, audit, and network sovereignty
   (`features/17_audit/`, `features/18_network_sovereignty/`, `features/19_identity_and_rbac/`,
   `features/21_policy_engine/`) — this layer is consulted by every other layer, not just
   invoked at the edges.

## Request path (typical)

UI → API (authn/authz/policy check) → Agent Kernel (plan) → Tool Gateway / Model Router (per
plan step, each individually permission- and policy-checked) → Evidence/Audit write → back to
UI, with any medium/high-risk step pausing at Human Approval before it executes.

## Data path

Uploaded documents flow: Document Ingestion → OCR/Multimodal (if needed) → Knowledge Fabric
(chunk, embed, index) → retrievable by the Agent Kernel with permission filtering applied at
retrieval time, never only at ingestion time.

## Why this shape

- **Every capability sits behind the same gateway pattern** (tool gateway, model router,
  policy engine) so that permission and audit logic is written once and enforced everywhere,
  per `13_DEVELOPER_RULES.md` rule 3.
- **The trust layer is horizontal, not a bolt-on** — every other layer calls into it rather
  than the trust layer calling into them, which is what makes "nothing leaves this machine"
  and "everything is audited" true by construction rather than by convention.

## Deployment modes

See `architecture/15_single_node_architecture.md` (V1 demo target),
`architecture/17_air_gapped_architecture.md`, `architecture/18_restricted_network_architecture.md`,
and `architecture/19_on_premise_architecture.md` for the specific topology variants this
architecture must support without code changes — only configuration changes
(`16_ENVIRONMENT_AND_CONFIGURATION.md`).

## Coverage map (per `SIH26117_Documentation_Refactor_Master_Prompt.txt` §34)

This file is the entry point for system-level understanding, but not every §34 topic is
inlined here — each below lives in the file best suited to it, cross-referenced rather than
duplicated:

| §34 topic | Lives in |
|---|---|
| Overall architecture, system boundaries, major components, data flow, security boundaries, deployment model | This file |
| Product vision | `01_PRODUCT_VISION.md` |
| Sovereignty model | `architecture/17-19_*.md`, `features/18_network_sovereignty/` |
| Agent model | `features/04_agent_kernel/` |
| Evidence model | `domain/13_evidence_model.md` |
| Industrial intelligence model | `industrial/`, `domain/20_asset_model.md`, `industrial/13_asset_knowledge_graph.md` |
| MVP scope | `08_BUILD_PHASES.md`, `reference/10_feature_matrix.md` |

## See also

`05_ARCHITECTURAL_PRINCIPLES.md` for the design principles behind these choices, and every
file under `architecture/` for the specific cross-cutting views (trust boundaries, failure
domains, scaling strategy, etc.) that this summary doesn't have room for.
