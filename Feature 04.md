# Feature 04 — OCR & Document Intelligence Pipeline

## Purpose
Lets the workbench "read" scanned reports/images (not just clean text PDFs) — this is the "inspect scanned reports" capability from your source doc, scoped to CPU-only via Tesseract rather than a VLM (see `03_HARDWARE_CONSTRAINTS.md` for why).

## How to build

1. **Detect document type on upload** — if a PDF has an extractable text layer, use direct text extraction (e.g. `pdfplumber`/`PyMuPDF`) and skip OCR entirely (much faster, more accurate). Only route to OCR when a page has no extractable text (scanned image) or the upload is a raw image file.
2. **Preprocessing for OCR** — convert PDF pages to images (`pdf2image`/`PyMuPDF` render), then basic preprocessing: grayscale, deskew if easy to add, threshold/binarize. This meaningfully improves Tesseract accuracy on scanned reports and is cheap on CPU.
3. **Run Tesseract** (`pytesseract`) per page, collect text + a confidence score. Store the extracted text per page alongside the doc's other pages so it merges seamlessly into the RAG ingestion pipeline (Feature 03) — OCR output should look identical downstream to normal extracted text.
4. **Confidence handling** — if Tesseract's average confidence for a page is below a threshold (e.g. 60), flag that page as "low confidence" in the execution graph rather than silently feeding possibly-garbled text into the model.
5. **Wire into the execution graph** — "OCR completed, N pages processed, M findings/pages flagged low-confidence" should appear as its own step, matching the example graph in your source doc (`✓ OCR completed`).

## Data/API contract

```json
{"doc_id": 12, "pages": [
  {"page": 1, "text": "...", "source": "text_layer"},
  {"page": 2, "text": "...", "source": "ocr", "confidence": 78},
  {"page": 3, "text": "...", "source": "ocr", "confidence": 41, "flagged_low_confidence": true}
]}
```

## Failure conditions

| Failure | Cause | Mitigation |
|---|---|---|
| OCR is too slow on the 8 GB demo box for a live upload | Tesseract on many pages, or high-DPI rendering before OCR | Cap rendered image DPI (150-200 is usually enough), pre-ingest the demo document set as in Feature 03, and only demo live-upload with a short (1-3 page) document |
| Garbled text silently poisons RAG answers | Low-confidence OCR output ingested without any signal | Enforce the confidence threshold + flag; optionally exclude flagged pages from retrieval by default and only include on explicit user request |
| Tesseract not installed / wrong language pack on demo machine | Environment drift between dev and demo box | Pin exact install steps (`apt install tesseract-ocr`) in your setup doc/README, and verify on the actual demo hardware before judging day, not just your dev machine |
| Scanned tables/forms extracted as unstructured garbage text | Tesseract does layout-blind text extraction by default | For the hackathon scope, accept this limitation and don't promise structured table extraction; if a demo document has a table, pick one where the surrounding narrative text carries the key finding |
| Rotated/skewed scan pages produce near-empty or nonsense output | No deskew/orientation correction | Use `pytesseract.image_to_osd` for orientation detection as a quick win, or manually ensure demo-day sample scans are upright |

## Definition of Done
Uploading a scanned (image-based) sample report produces per-page extracted text with confidence scores, low-confidence pages are visibly flagged, and the extracted text is queryable through the same RAG pipeline as a native-text document.
