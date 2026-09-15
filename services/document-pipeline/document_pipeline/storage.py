"""Object-storage stub.

The canonical object storage is MinIO (docs/06_TECHNOLOGY_STACK.md), which is not
available in this development environment. Per the dependency-graph rule
(docs/10_DEPENDENCY_GRAPH.md) this stub is an EXPLICIT stub, never a silent fake: it
implements the typed interface with a service-local directory backend and warns at
first use. The canonical OBJECT_STORAGE_* env keys (docs/16) will drive the real
adapter when it lands; per docs/16's rule (no new config keys) this stub introduces
no new environment variable (see docs/20_DECISION_LOG.md DEC-023).

The interface is the real contract: put/get/delete by content-keyed object name,
no local path semantics leaked into callers — swapping in the MinIO backend should
require no changes above this module.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import BinaryIO, Protocol

logger = logging.getLogger("document_pipeline.storage")

_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if not _WARNED:
        logger.warning(
            "ObjectStorageStub active: objects are written to a local directory. "
            "Replace with the MinIO adapter (OBJECT_STORAGE_* keys) before production "
            "— see docs/20_DECISION_LOG.md DEC-023."
        )
        _WARNED = True


class ObjectStorage(Protocol):
    """Typed interface for object storage (MinIO in production)."""

    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class StubObjectStorage:
    """Local-directory backend. Keys are opaque ids (document UUIDs), never paths."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        _warn_once()

    def _path(self, key: str) -> Path:
        if not key or "/" in key or "\\" in key or key in (".", ".."):
            raise ValueError("storage key must be a bare opaque id")
        return self.root / key

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def get(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise KeyError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()
