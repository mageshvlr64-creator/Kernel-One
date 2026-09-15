"""PyMuPDF adapter — docs/integrations/09_pymupdf.md contract, PDF failure modes from
docs/failures/21_pdf_failures.md.

Extracts (per the integration contract):
- page text with bounding boxes (for citation coordinates, domain/13_evidence_model.md)
- per-page image-render flags / image content flags (pages requiring OCR handoff)
- embedded tables where detectably present (structured table blocks)

Failure mapping (failures/21): a corrupted, password-protected, or unsupported PDF maps to
INVALID_REQUEST with a SPECIFIC reason — never a generic parse error. The empty-document
edge (no extractable text at all) marks the document scanned-candidate, not failed.

This adapter performs zero outbound network calls (feature doc acceptance criterion).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pymupdf  # PyMuPDF 1.24+: canonical import name (fitz alias deprecated)

logger = logging.getLogger("document_pipeline.pdf")

# A page is a scanned candidate when it has no real text layer. The signal is span
# presence: a page with zero non-whitespace spans (or only degenerate fragments below this
# small floor) has no text layer; genuinely-native pages virtually always exceed it.
MIN_TEXT_CHARS_PER_PAGE = 8


@dataclass
class TextSpan:
    text: str
    bbox: List[float]  # (x0, y0, x1, y1) page-space, for evidence citations


@dataclass
class PageExtraction:
    page_number: int  # 1-based, matches user-visible page numbering
    text: str
    spans: List[TextSpan] = field(default_factory=list)
    has_images: bool = False
    text_empty: bool = True
    tables: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ParseOutcome:
    ok: bool
    page_count: int
    pages: List[PageExtraction] = field(default_factory=list)
    scanned_candidate: bool = False  # every page text-empty -> OCR path (EXTRACTING -> OCR)
    failure_reason: str = ""         # specific operator detail when ok is False


class PdfParseError(Exception):
    """Raised for mapped, specific parse failures (failures/21_pdf_failures.md)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def parse_pdf(data: bytes) -> ParseOutcome:
    """Parse a PDF blob into structured pages with citations-grade coordinates."""
    try:
        doc = pymupdf.Document(stream=data, filetype="pdf")
    except Exception as exc:  # corrupted header / not a PDF at all
        raise PdfParseError(f"unreadable PDF structure: {exc}") from exc

    try:
        if doc.needs_pass:
            raise PdfParseError("password-protected PDFs are not supported")
        if doc.is_encrypted:
            raise PdfParseError("encrypted PDFs are not supported")
        page_count = doc.page_count
        if page_count < 1:
            raise PdfParseError("PDF contains no pages")

        pages: List[PageExtraction] = []
        all_empty = True
        for i in range(page_count):
            page = doc.load_page(i)
            text_dict = page.get_text("dict")
            spans: List[TextSpan] = []
            chunks: List[str] = []
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text.strip():
                            spans.append(TextSpan(text=text, bbox=list(span["bbox"])))
                            chunks.append(text)
            text = "\n".join(chunks)
            has_images = bool(page.get_images(full=False)) or bool(
                [b for b in text_dict.get("blocks", []) if b.get("type") == 1]
            )
            text_empty = len(text.strip()) < MIN_TEXT_CHARS_PER_PAGE
            if not text_empty:
                all_empty = False
            pages.append(PageExtraction(
                page_number=i + 1,
                text=text,
                spans=spans,
                has_images=has_images,
                text_empty=text_empty,
                tables=_detect_tables(page),
            ))

        return ParseOutcome(
            ok=True,
            page_count=page_count,
            pages=pages,
            scanned_candidate=all_empty,
            failure_reason="",
        )
    finally:
        doc.close()


def _detect_tables(page: "pymupdf.Page") -> List[Dict[str, Any]]:
    """Embedded tables where detectable (integration contract). Returns per-table metadata;
    full cell extraction is an increment for the table op (feature file 08)."""
    tables: List[Dict[str, Any]] = []
    try:
        found = page.find_tables()
    except Exception as exc:  # table detection is best-effort; a detector failure is not
        logger.debug("table detection failed on page: %s", exc)  # a document failure
        return tables
    for t in getattr(found, "tables", []) or []:
        tables.append({"bbox": list(t.bbox), "row_count": t.row_count, "col_count": t.col_count})
    return tables
