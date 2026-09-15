"""document-pipeline — Document Ingestion service.

Implements docs/features/10_document_ingestion/ per docs/15_CODEBASE_TARGET_STRUCTURE.md
(services/document-pipeline owns features/10_document_ingestion/, 11_ocr/, 12_multimodal/).

This increment covers feature group 10 only (ops: upload_validation, file_type_detection,
native_pdf_parsing, scanned_pdf_detection, page_extraction, metadata_extraction,
ingestion_overview). OCR (feature group 11) and the knowledge fabric (group 13) are hard
dependencies named by the feature docs and arrive as later increments; until then the
pipeline stops at INDEXING, which the canonical Document state machine permits
(EXTRACTING -> INDEXING is owned by Document Ingestion; INDEXING -> READY is owned by
Knowledge Fabric and is intentionally NOT triggered here).

Shared contracts implemented verbatim (read-only for this service):
- docs/reference/01_error_codes.md            -> errors.py
- docs/schemas/02_api_schema.md + api/26      -> api.py / errors.py envelope
- docs/schemas/15_audit_event_schema.md       -> audit.py
- docs/runtime/_state_machines_canonical.md   -> statemachine.py
- docs/runtime/11_retry_policy.md             -> retry.py
- docs/reference/05_permission_matrix.md      -> policy.py
- docs/domain/06 + schemas/07                 -> domain.py
"""

__version__ = "0.1.0"
