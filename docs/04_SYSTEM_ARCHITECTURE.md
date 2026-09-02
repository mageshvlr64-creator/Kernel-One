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
   (`features/15_artifact_engine/`).
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

## See also

`05_ARCHITECTURAL_PRINCIPLES.md` for the design principles behind these choices, and every
file under `architecture/` for the specific cross-cutting views (trust boundaries, failure
domains, scaling strategy, etc.) that this summary doesn't have room for.
