"""Shared fixtures for the knowledge-fabric test suite.

Coverage maps to the feature docs' Test requirements (§24) and Acceptance criteria
(§25): unit tests per Failure-modes row, one integration test per success path,
permission tests per role, and the exactly-one-audit-event invariant (§22).
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from knowledge_fabric.audit import InMemoryAuditSink
from knowledge_fabric.config import Settings
from knowledge_fabric.domain import DocumentRef
from knowledge_fabric.ops import Context, KnowledgeFabricService
from knowledge_fabric.policy import Actor
from knowledge_fabric.storage import ChunkIndex, DocumentSource


@pytest.fixture()
def settings():
    return Settings()


@pytest.fixture()
def sink():
    return InMemoryAuditSink()


@pytest.fixture()
def service(settings, sink):
    svc = KnowledgeFabricService(source=DocumentSource(),
                                 index=ChunkIndex(embedding_dim=settings.embedding_dim),
                                 audit_sink=sink, settings=settings)
    # A standing INDEXING document most tests index: workspace/classification visible
    # to the default INTERNAL-clearance actors.
    ref = DocumentRef(
        document_id=str(uuid.uuid4()), state="INDEXING", workspace_id="ws-dev",
        classification="INTERNAL", owner_id="dev:analyst",
        source_text=("Quarterly maintenance schedule for the boiler unit. " * 12)
        + "\n\nValve inspection is due in October. Safety review follows. " * 4)
    svc.source.upsert(ref)
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


def make_document(service, *, state="INDEXING", classification="INTERNAL",
                  workspace="ws-dev", text=None, owner="dev:analyst"):
    ref = DocumentRef(
        document_id=str(uuid.uuid4()), state=state, workspace_id=workspace,
        classification=classification, owner_id=owner,
        source_text=text if text is not None else
        ("Pump alignment procedure step by step. " * 10)
        + "\n\nCalibrate the sensor before reassembly. " * 3)
    service.source.upsert(ref)
    return ref


@pytest.fixture()
def call(service):
    """Direct in-process entry point (feature docs §12): invoke + unwrap."""
    def _call(actor, op, payload):
        return service.invoke(op, actor, payload)
    return _call
