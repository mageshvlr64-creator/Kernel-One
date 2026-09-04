# Inspection Report Q&A

> End-to-end workflow specification. References the specific features involved rather than
> restating their internal behavior.

## Requirements implemented

REQ-FUNC-001, REQ-FUNC-004, REQ-FUNC-005

## Steps

1. Administrator uploads a scanned inspection report PDF, classification=INTERNAL
2. Document state: UPLOADED → VALIDATING → EXTRACTING → OCR → INDEXING → READY
3. User asks: 'What findings indicate equipment below specification, and on what page?'
4. Agent retrieves relevant DocumentChunks via hybrid search (features/13_knowledge_fabric/09_hybrid_search.md)
5. Agent generates answer with Evidence records attached per claim (REQ-FUNC-005)
6. UI evidence panel (ui/09_evidence_panel.md) renders citations with page jump links

## Notes

This is the primary demo scenario — full detail in demo/01_demo_overview.md and demo/05_inspection_report_demo.md.
