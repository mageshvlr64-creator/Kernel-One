# Logical Architecture

> The five-layer logical view referenced by `04_SYSTEM_ARCHITECTURE.md`, expanded here with
> the specific responsibility of each layer and what it explicitly does not do.

## Layers and responsibilities

1. **UI layer** (`ui/`) — rendering and user interaction only; contains no authorization logic
   of its own (calls `POST /api/v1/rbac/check` for UX convenience, but never enforces).
2. **API layer** (`api/`) — request validation, authentication, and routing to the correct
   internal service; the first and last point where the `ApiSuccessEnvelope`/`ApiErrorEnvelope`
   (`schemas/02_api_schema.md`) shape is applied.
3. **Agent kernel layer** (`features/04_agent_kernel/`) — planning and orchestration only; does
   not itself implement any tool's logic or any model's inference.
4. **Capability layer** (Model Router, Inference Gateway, Tool Gateway + tools, Knowledge
   Fabric, Artifact Engine) — does the actual work each capability is named for; has no
   authority to bypass the trust layer below.
5. **Trust layer** (Identity, Policy Engine, Audit, Network Sovereignty) — horizontal, called
   by every layer above it, never the reverse.

## What logical layering does NOT mean

Layers are a logical/dependency-direction concept, not necessarily separate physical
processes in V1 (`architecture/15_single_node_architecture.md`) — several logical layers may
run in the same container for V1's single-node deployment while still respecting the
dependency direction, which is what makes later physical separation
(`architecture/16_multi_node_architecture.md`) possible without a rewrite.
