"""Shared fixtures for the document-pipeline test suite.

Test coverage maps to the feature docs' Test requirements (§24): unit tests per Failure
modes row, one integration test per full success path, permission tests per role, and the
Acceptance criteria (§25) including the exactly-one-audit-event invariant.
"""
from __future__ import annotations

import base64
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from document_pipeline.audit import InMemoryAuditSink          # noqa: E402
from document_pipeline.config import Settings                  # noqa: E402
from document_pipeline.ops import (DocumentIngestionService,   # noqa: E402
                                   OpError, execute)
from document_pipeline.policy import DEV_ACTOR_TOKENS, Actor   # noqa: E402
from document_pipeline.store import InMemoryDocumentStore      # noqa: E402
from document_pipeline.storage import StubObjectStorage        # noqa: E402


class FailingStorage(StubObjectStorage):
    """Stub that simulates the object-storage dependency being down."""

    def __init__(self) -> None:
        self.calls = 0

    def put(self, key, data):  # noqa: D102
        self.calls += 1
        raise ConnectionError("minio is down")


class FlakyStorage(StubObjectStorage):
    """Fails the first N puts, then succeeds — exercises the retry class."""

    def __init__(self, fail_times: int = 1) -> None:
        self.fail_times = fail_times
        self.calls = 0
        self.inner = StubObjectStorage(Path(".test-storage"))

    def put(self, key, data):  # noqa: D102
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("transient")
        return self.inner.put(key, data)

    def get(self, key):
        return self.inner.get(key)


@pytest.fixture()
def actors() -> dict:
    return {slug: DEV_ACTOR_TOKENS[f"dev-token-{slug}"]
            for slug in ("administrator", "security-officer", "operator",
                         "analyst", "restricted", "auditor")}


@pytest.fixture()
def service(tmp_path) -> DocumentIngestionService:
    return DocumentIngestionService(
        store=InMemoryDocumentStore(),
        storage=StubObjectStorage(tmp_path / "objects"),
        audit_sink=InMemoryAuditSink(),
        settings=Settings(),
    )


@pytest.fixture()
def audit_sink(service) -> InMemoryAuditSink:
    return service.audit


@pytest.fixture()
def call(service):
    """invoke an op as an actor; raises OpError on failure (like the HTTP layer)."""
    def _call(actor: Actor, op: str, payload: dict):
        return execute(service, _ctx(actor), op, payload)
    return _call


def _ctx(actor: Actor):
    from document_pipeline.ops import Context
    return Context(actor=actor, source_ip="127.0.0.1")


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def make_pdf(pages: int = 2, text: str | None = None, *, scanned: bool = False) -> bytes:
    """Build a real PDF with PyMuPDF so the adapter is exercised against genuine files."""
    import pymupdf
    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        if scanned:
            # Draw only pixels (a rectangle), no text -> text-empty page.
            page.draw_rect(pymupdf.Rect(50, 50, 300, 300), color=(0, 0, 0), width=1)
        else:
            page.insert_text((72, 100), text or f"Page {i + 1} of {pages}: "
                             "lorem ipsum industrial maintenance procedure")
    return doc.tobytes()


def text_payload(actors_, content: str = "asset_id,priority\nA-1,high\n", **overrides) -> dict:
    payload = {"filename": "maintenance.csv", "content_base64": b64(content.encode("utf-8"))}
    payload.update(overrides)
    return payload


def pdf_payload(actors_, data: bytes, **overrides) -> dict:
    payload = {"filename": "spec.pdf", "content_base64": b64(data)}
    payload.update(overrides)
    return payload


def run_pdf_pipeline(call, actor: Actor, data: bytes) -> dict:
    """upload -> validate -> parse, returning the parse result data."""
    up = call(actor, "upload_validation", pdf_payload(actor, data))
    call(actor, "file_type_detection", {"document_id": up.resource_id})
    parsed = call(actor, "native_pdf_parsing", {"document_id": up.resource_id})
    return {"upload": up, "parsed": parsed, "document_id": up.resource_id}
