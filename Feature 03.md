# Feature 03 — Local RAG (Retrieval-Augmented Generation)

## Purpose
Lets the workbench answer questions grounded in uploaded confidential documents instead of the model's own (untrustworthy, possibly hallucinated) knowledge — and, combined with Feature 08, lets every answer cite its source.

## How to build

1. **Ingestion** — on document upload, extract text (direct text extraction for PDFs/docx; hand image-only pages to OCR, Feature 04). Chunk text into ~300-500 token windows with ~50-token overlap. Simple recursive character/paragraph splitting is enough; don't build a fancy semantic chunker in 14 days.
2. **Embedding** — embed each chunk with `all-MiniLM-L6-v2` (CPU, fast, small). Store `{chunk_id, doc_id, page_no, text, embedding}` in Chroma (or FAISS index + a parallel SQLite table for metadata if you switch).
3. **Retrieval** — on a `document_qa` task, embed the user's question with the same model, run a top-k (k=3-5) similarity search, and pass the retrieved chunk texts into the LLM prompt as context, clearly delimited (e.g. `<context>...</context>`).
4. **Prompt construction** — instruct the model explicitly: "Answer only using the provided context. If the answer isn't in the context, say so." This single instruction is your main defense against hallucination in the demo.
5. **Corpus scope for the demo** — pre-load 3-5 realistic sample documents (inspection reports, SOPs) so the RAG demo isn't dependent on a live, possibly slow, upload+ingest during judging.

## Data/API contract

```json
// retrieval result passed to generation step
{"chunks": [
  {"doc_id": 12, "page": 3, "text": "...", "score": 0.81},
  {"doc_id": 12, "page": 7, "text": "...", "score": 0.77}
]}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| Model answers confidently from outside the context (hallucination) | Prompt doesn't strongly constrain the model, or context wasn't actually retrieved (empty result silently passed through) | Explicit "answer only from context / say 'not found' otherwise" instruction; if retrieval returns 0 chunks above a similarity threshold, skip generation and return "no relevant information found" directly |
| Retrieval returns irrelevant chunks | Chunk size too large/small for the corpus, or embedding model mismatch between ingestion and query time | Keep chunk size in the 300-500 token range; always use the exact same embedding model/version for ingestion and query |
| Ingestion is slow enough to stall the live demo | Embedding a large document synchronously in the request path | Pre-ingest demo documents before judging; for any live-upload part of the demo, show it as a background/async step in the execution graph rather than blocking |
| Chroma/FAISS index grows unbounded across dev sessions and eats demo-machine disk/RAM | No cleanup between test runs | Add a `reset_corpus()` dev utility; keep the demo-day corpus small and deliberate (a handful of docs, not every test file you ever ingested) |
| Citations point to the wrong page/chunk | Metadata (`page_no`) not correctly propagated from the PDF parser through chunking into the vector store | Unit-test that a known chunk's stored `page_no` matches the source PDF page for at least one hand-checked document before demo day |

## Definition of Done
Asking a question about a pre-loaded sample document returns an answer that (a) is grounded only in retrieved chunks, (b) explicitly says "not found" when asked something outside the corpus, and (c) the retrieval step is visible in the execution graph with the doc_id/chunk count shown.
