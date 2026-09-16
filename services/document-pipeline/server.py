"""document-pipeline entrypoint.

Runs the HTTP API for the Document Ingestion service (feature group 10). Configuration
comes from the canonical env keys (docs/16); dependencies use the explicit stubs noted in
DEC-023 until their canonical integrations land:

- object storage: StubObjectStorage (local directory)      <- MinIO later
- documents store: InMemoryDocumentStore (non-durable)     <- PostgreSQL later
- audit sink: InMemoryAuditSink (ordered, hash-chained)    <- audit-service later
- auth: DEV_ACTOR_TOKENS bearer stub                        <- identity-service later
- industrial enrichment (upload_validation optional): LIVE client to
  industrial-service /internal/resolve-tag + /internal/validate-finding —
  real HTTP calls, fired only when an upload payload carries the optional
  equipment_tag/finding extensions (Character-3 wiring named in the
  industrial changelog)

Usage:  python server.py [--host HOST] [--port PORT]
"""
from __future__ import annotations

import argparse
import logging
import sys

from document_pipeline.api import Api, serve
from document_pipeline.audit import InMemoryAuditSink
from document_pipeline.config import load_settings
from document_pipeline.ops import DocumentIngestionService
from document_pipeline.store import InMemoryDocumentStore
from document_pipeline.storage import StubObjectStorage


def build_service():
    settings = load_settings()
    logging.basicConfig(level=settings.log_level.upper(),
                        format="%(levelname)s %(name)s %(message)s")
    sink = InMemoryAuditSink()
    store = InMemoryDocumentStore()
    storage = StubObjectStorage(settings.storage_dir)
    return DocumentIngestionService(store=store, storage=storage,
                                    audit_sink=sink, settings=settings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="document-pipeline service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args(argv)

    service = build_service()
    api = Api(service)
    server = serve(api, args.host, args.port)
    logging.getLogger("document_pipeline").info(
        "document-pipeline listening on http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
