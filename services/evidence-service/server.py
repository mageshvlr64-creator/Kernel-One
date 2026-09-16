"""evidence-service entrypoint.

Runs the HTTP API for the Evidence & Provenance service (feature group 14,
build-order #17). Configuration from canonical env keys (docs/16); dependencies
use the explicit stubs noted in the module docstrings and DEC-023 until the
canonical integrations land:

- evidence_links store: in-process dict          <- PostgreSQL table later
- source chain facts: seeded in-process view     <- documents API (document-pipeline) later
- retrieval view (chunks): seeded in-process     <- knowledge-fabric API later
- audit sink: InMemoryAuditSink (hash-chained)   <- audit-service (Character 5) later
- auth: dev bearer-token stub (deny-by-default)  <- identity-service (Character 5) later

Usage:  python server.py [--host HOST] [--port PORT]
"""
from __future__ import annotations

import argparse
import logging
import sys

from evidence_service.api import Api, serve
from evidence_service.audit import InMemoryAuditSink
from evidence_service.claims import ClaimStore
from evidence_service.config import load_settings
from evidence_service.ops import EvidenceService
from evidence_service.storage import EvidenceLinks, RetrievalView, SourceChainStore


def build_service():
    settings = load_settings()
    logging.basicConfig(level="INFO", format="%(levelname)s %(name)s %(message)s")
    return EvidenceService(links=EvidenceLinks(), claims_store=ClaimStore(),
                           chains=SourceChainStore(), retrieval=RetrievalView(),
                           audit_sink=InMemoryAuditSink(), settings=settings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="evidence-service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args(argv)

    service = build_service()
    api = Api(service)
    server = serve(api, args.host, args.port)
    logging.getLogger("evidence_service").info(
        "evidence-service listening on http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
