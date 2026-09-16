"""Shared fixtures for the evidence-service test suite.

Coverage maps to the feature docs' Test requirements (§24) and Acceptance
criteria (§25): unit tests per Failure-modes row, integration tests per success
path, permission tests per role, and the exactly-one-audit-event invariant (§22).
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evidence_service.audit import InMemoryAuditSink          # noqa: E402
from evidence_service.claims import ClaimStore                # noqa: E402
from evidence_service.config import Settings                  # noqa: E402
from evidence_service.ops import EvidenceService              # noqa: E402
from evidence_service.policy import Actor                     # noqa: E402
from evidence_service.storage import (EvidenceLinks,          # noqa: E402
                                      RetrievalView, SourceChainStore)


@pytest.fixture()
def settings():
    return Settings()


@pytest.fixture()
def sink():
    return InMemoryAuditSink()


@pytest.fixture()
def service(settings, sink):
    svc = EvidenceService(links=EvidenceLinks(), claims_store=ClaimStore(),
                          chains=SourceChainStore(), retrieval=RetrievalView(),
                          audit_sink=sink, settings=settings)
    return svc


def make_actor(role="Analyst", clearance="INTERNAL", workspace="ws-dev"):
    return Actor(actor_id=f"dev:{role.lower().replace(' ', '-')}", role=role,
                 clearance=clearance, workspace_id=workspace)


@pytest.fixture()
def analyst():
    return make_actor("Analyst")


@pytest.fixture()
def admin():
    return make_actor("Administrator")


@pytest.fixture()
def auditor():
    return make_actor("Auditor")


@pytest.fixture()
def restricted():
    return make_actor("Restricted User", clearance="PUBLIC")


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


DOC_ID = "11111111-1111-4111-8111-111111111111"
CHUNK_ID = "22222222-2222-4222-8222-222222222222"
TASK_ID = "33333333-3333-4333-8333-333333333333"


def seed_chain(service, *, document_id: str = DOC_ID, version: int = 1,
               authority: str = "primary", superseded_by: str | None = None,
               effective_from: str | None = "2024-01-01T00:00:00Z",
               effective_until: str | None = None):
    return service.chains.seed_document(document_id, version, _sha(f"doc-{document_id}-v{version}"),
                                        authority, effective_from=effective_from,
                                        effective_until=effective_until)


def seed_chunk(service, *, chunk_id: str = CHUNK_ID, document_id: str = DOC_ID,
               page_number: int | None = 3, bbox: list | None = None):
    return service.retrieval.seed_chunk(
        chunk_id, document_id, chunk_index=0, page_number=page_number,
        bbox=bbox if bbox is not None else [72.0, 100.0, 300.0, 140.0],
        text="The relief valve set pressure is 150 psi per section 4.2.")


def evidence_payload(**overrides) -> dict:
    payload = {
        "task_id": TASK_ID,
        "source_document_id": DOC_ID,
        "document_version": 1,
        "chunk_id": CHUNK_ID,
        "source_hash": _sha("doc"),
        "retrieval_method": "hybrid",
        "source_authority": "primary",
        "confidence": 0.83,
        "page_number": 3,
        "section_reference": "§4.2",
    }
    payload.update(overrides)
    return payload


def create_evidence(service, actor, **overrides):
    """Seed chain + chunk + one evidence row; returns the OpResult."""
    seed_chain(service, document_id=overrides.get("source_document_id", DOC_ID),
               version=overrides.get("document_version", 1),
               authority=overrides.get("source_authority", "primary"))
    seed_chunk(service, chunk_id=overrides.get("chunk_id", CHUNK_ID),
               document_id=overrides.get("source_document_id", DOC_ID),
               page_number=overrides.get("page_number", 3))
    return service.invoke("evidence_system", actor, evidence_payload(**overrides))


def make_answer_text() -> str:
    return ("The relief valve set pressure is 150 psi. "
            "Inspection is due in October. "
            "The sky is green.")


@pytest.fixture()
def call(service):
    """Direct in-process entry point (feature docs §12): invoke + unwrap."""
    def _call(actor, op, payload):
        return service.invoke(op, actor, payload)
    return _call
