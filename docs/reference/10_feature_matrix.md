# Feature Matrix (Reference)

> V1-committed vs. V1-aspirational vs. V2 status for every feature group, consolidating the
> per-directory scope notes scattered across `features/`, `industrial/`, and `later/`.

| Feature group | Status | Notes |
|---|---|---|
| 01-09 (Model Management through Code Execution) | V1-committed | Core platform, demo-critical |
| 10-15 (Document Ingestion through Artifact Engine) | V1-committed | Core RAG/evidence/artifact pipeline |
| 16-21 (Human Approval through Policy Engine) | V1-committed | Trust layer, demo-critical |
| 22 (Agent Memory) | V1-committed, basic scope | Conversation/task memory; no cross-session long-term memory in V1 |
| 23 (Spreadsheet Intelligence) | V1-committed | Supporting workflow, not the primary demo path |
| 24-26 (Admin Console, Observability, Backup/Recovery) | V1-committed | Operational necessities |
| Industrial: inspection reports, engineering calculations | V1-committed | `industrial/12_industrial_workflow_boundaries.md` |
| Industrial: P&ID/drawing intelligence | V1-aspirational | Explicitly caveated if present |
| Voice (speech/TTS), multi-node, Kubernetes, enterprise identity | V2 (`later/`) | Not attempted in V1 under any circumstance |

## Rule

A feature's status here must match its own file's scope statement — this table is a summary,
not an independent source of truth (the feature's own directory is authoritative).
