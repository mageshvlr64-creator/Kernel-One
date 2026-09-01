SIH26117 — Sovereign AI Workbench — Documentation Set

**Team code:** SIH26117
**Situation assumed (stated by you):** solo build, ~2 weeks (14 days), no teammates mentioned.
**Dev machine:** 16 GB RAM, no GPU (CPU-only inference)
**Demo machine:** 8 GB RAM, no GPU (CPU-only inference)

> If you actually do have 2-3 teammates, say so — the day-by-day plan in `04_BUILD_PLAN.md` splits cleanly into 3 parallel tracks (Router/Backend, Agent/Tools, UI/Artifacts) and finishes faster. Everything else in this doc set stays the same either way.

## What this doc set is

This is **documentation only** — no application code. Each file tells you (or a teammate) exactly what to build, in what order, with what libraries, and what will go wrong if you're not careful. Feed each `features/*.md` file to a coding assistant one at a time and it has everything needed to implement that feature correctly.

## Folder structure

```
docs/
├── 00_README.md                  <- you are here
├── 01_ARCHITECTURE.md            <- system diagram, layer responsibilities
├── 02_STACK.md                   <- exact stack recommendation for 8GB/no-GPU
├── 03_HARDWARE_CONSTRAINTS.md    <- what NOT to attempt given your hardware
├── 04_BUILD_PLAN.md              <- day-by-day 14-day plan
├── 05_DEMO_SCRIPT.md             <- the actual judge-facing demo flow
└── features/
    ├── 01_model_router.md
    ├── 02_agent_kernel.md
    ├── 03_local_rag.md
    ├── 04_ocr_document_intelligence.md
    ├── 05_tool_execution_gateway.md
    ├── 06_sandboxed_code_execution.md
    ├── 07_artifact_engine.md
    ├── 08_evidence_and_citations.md
    ├── 09_human_approval_system.md
    ├── 10_audit_log.md
    ├── 11_network_sovereignty_monitor.md
    └── 12_rbac.md
```

## Reading order

1. `01_ARCHITECTURE.md` — understand the shape before building anything.
2. `02_STACK.md` + `03_HARDWARE_CONSTRAINTS.md` — lock the stack so you don't waste days on a model/library that can't run on 8 GB CPU-only.
3. `04_BUILD_PLAN.md` — the day-by-day order. Features are built in **dependency order**, not difficulty order — the plan tells you why.
4. `features/*.md` in the numbered order — build each one to its "Definition of Done" before moving to the next.
5. `05_DEMO_SCRIPT.md` — write this in parallel with the build so the last 2 days are polish, not scrambling to invent a demo.

## Ground truth this doc set assumes

- The original 4000-line plan you uploaded assumed **GPU access "later"** for the demo. You told me: no GPU on either machine, 8 GB on the demo box. That single fact eliminates gpt-oss-20B, most VLMs, and anything needing >4 GB of resident model weights. `03_HARDWARE_CONSTRAINTS.md` explains exactly what that rules in and out.
- V1 scope is the original plan's own "final scope" (Section 34 of your doc): Model Router, Agent Kernel, Local RAG, OCR/Doc Intelligence, Tool Execution, Sandboxed Python, Artifact Engine, Evidence/Citations, Human Approval, Audit Log, Network Sovereignty Monitor, RBAC. Nothing beyond this — no P&ID intelligence, no multi-tenancy, no industrial calculation engine. Those are explicitly out of scope for a 14-day solo build.
