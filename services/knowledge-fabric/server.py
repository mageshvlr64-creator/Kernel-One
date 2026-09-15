"""knowledge-fabric entrypoint.

Runs the HTTP API for the Knowledge Fabric service (feature group 13). Configuration
from canonical env keys (docs/16); dependencies use the explicit stubs noted in the
module docstrings and DEC-023 until canonical integrations land:

- document source: DocumentSource stub (in-process view)    <- documents API later
- chunk index: ChunkIndex stub (in-memory + cosine)         <- PostgreSQL + pgvector later
- embedding: hash-based stub vectors (768-dim)              <- model-inference seam later
- audit sink: InMemoryAuditSink (ordered, hash-chained)     <- audit-service later
- auth: DEV_ACTOR_TOKENS bearer stub (deny-by-default)      <- identity-service later

Usage:  python server.py [--host HOST] [--port PORT]
"""
from __future__ import annotations

import argparse
import logging
import sys

from knowledge_fabric.api import Api, serve
from knowledge_fabric.audit import InMemoryAuditSink
from knowledge_fabric.config import load_settings
from knowledge_fabric.ops import KnowledgeFabricService
from knowledge_fabric.storage import ChunkIndex, DocumentSource


def build_service():
    settings = load_settings()
    logging.basicConfig(level=settings.log_level.upper()
                        if hasattr(settings, "log_level") else "INFO",
                        format="%(levelname)s %(name)s %(message)s")
    return KnowledgeFabricService(source=DocumentSource(), index=ChunkIndex(
        embedding_dim=settings.embedding_dim), audit_sink=InMemoryAuditSink(),
        settings=settings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="knowledge-fabric service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args(argv)

    service = build_service()
    api = Api(service)
    server = serve(api, args.host, args.port)
    logging.getLogger("knowledge_fabric").info(
        "knowledge-fabric listening on http://%s:%d", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
