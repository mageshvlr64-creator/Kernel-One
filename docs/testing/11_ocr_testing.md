# OCR Testing

> Covers `features/11_ocr/` specifically — accuracy and confidence reporting.

## Required tests

- `TEST-OCR-001`: the reference scanned inspection-report demo page
  (`demo/03_demo_data.md`) is fully and correctly extracted, satisfying REQ-AI-002's
  acceptance criterion.
- Low-quality/degraded scan input produces low `ocr_confidence` scores rather than
  high-confidence garbage text — confidence scoring itself is tested, not just extraction.
