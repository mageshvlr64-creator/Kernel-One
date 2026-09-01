# Feature 08 — Evidence & Citations

## Purpose
Your source doc calls this "the killer RAG feature: evidence graph." Every claim the model makes about a document should be traceable to the exact chunk/page it came from — this is what separates "an LLM summarized your document" (untrustworthy) from "here's the finding, and here's exactly where it came from" (auditable, trustworthy for confidential/industrial use).

## How to build

1. **Carry chunk metadata through generation** — when RAG (Feature 03) retrieves chunks, keep `{doc_id, page, chunk_id}` attached to each chunk all the way into the prompt, not just the raw text. Label each chunk in the prompt, e.g. `[C1] (doc 12, p.3): "..."`, `[C2] (doc 12, p.7): "..."`.
2. **Ask the model to cite by label** — instruct the model to reference `[C1]`/`[C2]` style labels inline when making a claim, e.g. "The pressure valve was found faulty [C1]." This is far more reliable from a small local model than asking it to reproduce exact page numbers from memory.
3. **Post-process citations** — after generation, regex-parse the `[C1]`-style labels out of the model's response and replace them with resolved, clickable references (`doc 12, page 3`) using your held metadata map — don't trust the model to get the page number right unaided; you already know it from the retrieval step.
4. **UI rendering** — render citations as small clickable chips after each sentence/claim; clicking one shows the exact source chunk text in a side panel, ideally with the source document highlighted at that location if time allows (a simple text-snippet popover is enough for 14 days — full PDF-viewer highlighting is a stretch goal, not required).
5. **Attach to audit log** — the citation map (`claim → chunk_id → doc_id/page`) for a task is stored alongside the task's audit trail, so "what did the AI base this on" is answerable after the fact, not just live in the UI.

## Data/API contract

```json
{"answer_text": "The pressure valve was found faulty [C1] and requires replacement [C2].",
 "citations": {
   "C1": {"doc_id": 12, "page": 3, "chunk_id": "c_88", "snippet": "..."},
   "C2": {"doc_id": 12, "page": 7, "chunk_id": "c_91", "snippet": "..."}
 }}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Model cites a label that wasn't actually provided (hallucinated `[C5]` when only C1-C3 existed) | No validation of citation labels against the retrieved set | Post-process step must validate every citation label against the known chunk set; drop/flag unresolvable citations rather than rendering a broken link |
| Model makes claims with no citation at all | Prompt doesn't strongly require citing, or model ignores instruction (common with small models) | Treat uncited factual sentences as lower-confidence in the UI (e.g. no citation chip shown, or a visible "unsourced" marker) rather than silently presenting them as equally grounded |
| Citation points to the right doc but wrong page | Metadata propagation bug between chunking and prompt construction (see also Feature 03's failure table) | Same fix as Feature 03: unit-test page metadata integrity on at least one hand-checked document |
| Citation UI adds too much complexity/time for a 14-day build | Trying to build full PDF-highlight-on-click before basics work | Ship the simple version first (clickable chip → snippet popover); only add PDF-position highlighting if Day 13/14 has slack |
| Citations aren't persisted, so re-opening a past task loses them | Citation map only kept in-memory / in the live WebSocket message | Persist the citation map to the audit/task DB alongside the answer text at generation time |

## Definition of Done
A demo answer about the sample inspection report shows at least 2 distinct, correct citations, each clickable to the correct source snippet, and any claim the model makes without a valid citation is visually distinguishable from cited claims.
