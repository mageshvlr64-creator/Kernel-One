# Architecture

## Why this shape (not a plain chatbot)

The judge-facing differentiator from your source doc is: **every AI action is controlled, auditable, permission-aware, reproducible, and locally executable.** That means the model is never allowed to touch a tool, file, or document directly. Everything passes through a policy layer first. This is the single architectural decision that separates you from an Open WebUI clone, so don't compromise on it under time pressure — it's cheap to build if you build it from Day 1, expensive to retrofit.

## Layer diagram

```
                        USER (browser)
                             │
                             ▼
                     WORKBENCH UI (React/HTML)
                             │  REST/WebSocket
                             ▼
                  ┌─────────────────────────┐
                  │   POLICY / RBAC LAYER    │  <- every request passes here first
                  └────────────┬────────────┘
                               ▼
                  ┌─────────────────────────┐
                  │      AGENT KERNEL        │  <- builds & executes the task graph
                  └────────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
        MODEL ROUTER      TOOL GATEWAY        KNOWLEDGE (RAG)
              │                │                   │
     ┌────────┼────────┐  ┌────┼─────┐      ┌──────┼──────┐
     ▼        ▼        ▼  ▼    ▼     ▼      ▼      ▼      ▼
  small-LLM coder-LLM OCR  FS  SANDBOX CALC  vector-DB  doc-parser  citations

                               │
                               ▼
                     ARTIFACT ENGINE (docx/xlsx/pdf)
                               │
                               ▼
                  HUMAN APPROVAL  →  AUDIT LOG (append-only)
```

## Layer responsibilities (one sentence each)

| Layer | Responsibility | Lives in |
|---|---|---|
| Workbench UI | Renders chat + live execution-graph status (the "✓ OCR completed / ⚠ Human approval required" view) | frontend/ |
| Policy/RBAC | Checks who the user is and what they're allowed to touch, before the kernel runs anything | backend/policy/ |
| Agent Kernel | Turns one user request into an ordered execution graph (plan → retrieve → call tool → verify → generate → approve) | backend/kernel/ |
| Model Router | Picks the smallest model capable of the subtask; never lets the app hardcode a model name | backend/router/ |
| Tool Gateway | The ONLY thing allowed to touch the filesystem, sandbox, or calculator — models never call tools directly | backend/tools/ |
| Knowledge/RAG | Chunk, embed, retrieve, and attach evidence spans to every claim | backend/rag/ |
| Artifact Engine | Turns verified output into a downloadable docx/xlsx/pdf | backend/artifacts/ |
| Audit Log | Append-only record of every kernel step, tool call, and approval decision | backend/audit/ (SQLite) |

## Non-negotiable rule for the whole build

**The LLM never calls a tool directly.** It emits a structured "I want to call tool X with args Y" message; the Tool Gateway validates it against RBAC + policy, executes it, and returns a structured result. This is what makes the audit log complete and the "sovereign execution environment" claim true rather than marketing. Every feature doc in `features/` assumes this rule.

## What "execution graph" means concretely

Each user task becomes a row-set in the audit DB and a JSON object like:

```json
{
  "task_id": "uuid",
  "steps": [
    {"name": "classify_request", "status": "done"},
    {"name": "select_model", "status": "done", "detail": "qwen2.5-1.5b-instruct-q4"},
    {"name": "retrieve_context", "status": "done", "detail": "3 chunks, doc_id=42"},
    {"name": "call_tool:ocr", "status": "done"},
    {"name": "generate_answer", "status": "done"},
    {"name": "human_approval", "status": "pending"}
  ]
}
```

The UI subscribes to this over a WebSocket and renders it live — this single object is what makes your demo look like a real product instead of a chat window.
