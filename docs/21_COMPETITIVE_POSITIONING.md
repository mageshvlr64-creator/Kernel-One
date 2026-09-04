# Competitive / Prior-Art Positioning

> Architectural comparison, not marketing. Purpose: make explicit what this project shares
> with existing self-hosted AI platforms, what it adds, and what it deliberately omits — so a
> reviewer can judge the actual delta rather than assume novelty by default.

## Comparable projects

| Project | What it is | Overlap with this project |
|---|---|---|
| **Open WebUI** | Self-hostable chat UI over Ollama/OpenAI-compatible backends | Chat interface, local model support, basic RBAC |
| **AnythingLLM** | Self-hostable RAG + agent workspace | Document RAG, workspace concept, multi-model support |
| **LibreChat** | Self-hostable multi-provider chat UI with plugins | Chat UI, tool/plugin calling, multi-user |
| **Dify** | Self-hostable LLM app-building platform with workflow orchestration | Agent/workflow orchestration, tool integration |
| **NVIDIA NIM / AI Enterprise** | Enterprise-grade self-hosted model serving and RAG toolkit | Model serving abstraction, enterprise deployment focus |

## What this project shares with them

- Self-hosted, on-prem-capable model serving (all five comparables support this to varying
  degrees).
- Local RAG over uploaded documents (Open WebUI, AnythingLLM, Dify).
- Tool/plugin calling from an agent loop (LibreChat, Dify).
- Role-based multi-user access (all five, to varying granularity).

## What this project adds

- **Formal, mandatory evidence/provenance model (REQ-FUNC-005):** none of the five comparables
  make citation-to-source-passage a hard architectural requirement with a defined refusal
  behavior when evidence can't be attached — it's typically a UI nicety, not an enforced
  invariant with its own failure mode and test (`TEST-EVIDENCE-001`).
- **Human approval as a first-class state machine (REQ-FUNC-003):** approval gating exists in
  some form in Dify's workflow builder, but not as a system-wide, classification-driven,
  auditable gate applied uniformly across tool calls, exports, and artifact generation.
- **Live, continuously-verified network sovereignty proof (REQ-NET-003):** "runs offline" is a
  deployment claim in all five comparables; a real-time UI panel plus a packet-capture-backed
  test (`TEST-NET-001`) proving zero egress during actual operation is not a standard feature
  of any of them.
- **Data classification propagation through the full pipeline (REQ-DATA-001):** classification
  levels that restrict which *model* may even see a document, propagated through evidence and
  artifacts, is closer to an enterprise DLP concern than a typical open-source chat/RAG tool's
  scope.
- **MoE-aware, explicit hardware-fit routing (REQ-AI-003):** the total-vs-active-parameter
  distinction is a common deployment mistake this project's router is explicitly built not to
  make; general-purpose chat UIs typically leave hardware sizing to the operator's judgment.

## What this project intentionally does not implement

- **No app-builder/workflow-canvas UI** (unlike Dify) — plans are agent-generated, not
  visually authored by end users, for V1.
- **No plugin marketplace / community extension ecosystem** (unlike LibreChat, Open WebUI) —
  tools are a fixed, audited, centrally-registered set (`features/05_tool_gateway/`), by
  design, because an open plugin ecosystem is in tension with REQ-SEC-002/REQ-SEC-001's
  closed, auditable tool surface.
- **No cloud-provider fallback mode** — REQ-NET-001/Rule 11 categorically excludes it, whereas
  Open WebUI/LibreChat/AnythingLLM commonly support cloud model providers as a first-class,
  equally-weighted option.

## Why the target use case changes the requirements

Confidential/regulated industrial environments treat "can this run offline" and "can I prove
nothing left the building" as procurement gates, not features — this shifts network
sovereignty, audit, classification, and evidence from "nice to have" into REQ-P0 territory,
which is why this specification's Section 28-30 equivalents (`features/18_network_sovereignty/`,
`features/17_audit/`, `features/20_data_classification/`) are far more heavily specified than
the equivalent concerns in general-purpose self-hosted AI tooling.

This is a positioning statement, not a competitive claim of superiority — each comparable
project optimizes for a different primary user (individual/hobbyist self-hosting, internal
dev tooling, enterprise app-building) and makes reasonable tradeoffs for that user that would
be wrong for this project's target user, and vice versa.
