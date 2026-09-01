# 14-Day Build Plan (solo, no-GPU, 8 GB demo target)

This reorders your source doc's day-by-day sketch (Section 37) around **dependency order**: nothing downstream works until the Agent Kernel + Model Router + Tool Gateway exist, so those come first, not last. Each day ends with a runnable, demoable increment — never leave the app in a broken state overnight.

If it turns out you DO have 2-3 teammates: split after Day 3 into Track A (Router+Kernel+Tools, backend-heavy person), Track B (RAG+OCR+Evidence, ML-leaning person), Track C (UI+Artifacts+Approval, frontend-leaning person), reconvening for integration on Day 10 and 13.

| Day | Build | Definition of done |
|---|---|---|
| 1 | Skeleton: FastAPI backend, minimal UI (chat box), **mock model** (hardcoded/random responses) wired end-to-end over WebSocket | Typing a message in the browser gets a fake response back through the full stack |
| 2 | Model Router v1 + real small model (Qwen2.5-1.5B via Ollama) replaces the mock | Real model answers general questions; router logs which model it picked |
| 3 | Agent Kernel v1: task → execution graph → steps rendered live in UI | UI shows the "✓ step / ⚠ pending" checklist for a simple 2-step task |
| 4 | Tool Gateway + RBAC skeleton (single admin user + one restricted user role) | A tool call is rejected for the restricted role and allowed for admin, both logged |
| 5 | Sandboxed Python execution tool | "Write and run a Python script" request executes in the sandbox with resource limits and returns output/errors |
| 6 | Local RAG: chunk + embed + retrieve (Chroma + MiniLM) over a small uploaded document set | Asking a question about an uploaded doc returns an answer grounded in retrieved chunks |
| 7 | Evidence & citations: attach source chunk/page to every RAG-backed claim | UI shows "[source: report.pdf, p.3]" style citations, clickable to the source snippet |
| 8 | OCR + document intelligence pipeline (Tesseract) | Uploading a scanned/image PDF produces extracted text that feeds into RAG |
| 9 | Artifact Engine: generate a DOCX approval note / summary from verified output | Clicking "generate report" downloads a real .docx with the model's findings |
| 10 | Human Approval system: pause execution graph at a defined step, require explicit user click to proceed | A task visibly halts at "⚠ Human approval required" until approved, then resumes |
| 11 | Audit Log: every kernel step, tool call, and approval decision persisted and viewable | An "Audit" screen lists every action taken for a given task, timestamped, immutable |
| 12 | Network Sovereignty Monitor: visible proof no outbound network call left the box during a task | UI shows a live "0 external requests" indicator or a log of blocked attempts during a demo run |
| 13 | Integration pass + spreadsheet intelligence stretch (openpyxl-based Excel Q&A) if time allows | Full pipeline (upload → OCR → RAG → agent → tool → artifact → approval → audit) runs without manual intervention |
| 14 | Demo polish: rehearse `05_DEMO_SCRIPT.md`, fix the top 3 failure conditions you hit during rehearsal, record the fallback screen capture | 3 successful dry runs on demo-equivalent hardware |

## Rules for staying on schedule

- **Don't reorder this list to do "fun" features early.** Router/Kernel/Tools/RBAC (Days 1-4) are boring but everything else is built on top of them — building RAG or Artifacts first means rebuilding them once the kernel exists.
- **Cut scope inside a day, not across days.** If Day 6's RAG is behind schedule, ship retrieval without re-ranking rather than pushing RAG into Day 7's slot.
- **Everything not in the 12-feature V1 list is out**, full stop, until Day 14 is done and stable: no P&ID intelligence, no multi-tenancy, no industrial calculation engine, no admin console beyond what RBAC needs.
