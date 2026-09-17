"""Audit event builder — docs/schemas/15_audit_event_schema.md (canonical, read-only).

Every invocation of an ingestion op — success, error, or denial — produces exactly one
AuditEvent conforming to this schema. The tamper-evident chain (prev_event_hash) and the
INSERT-only storage rules are enforced by audit-service (Character 5's feature group 17);
this module emits schema-valid events into the sink it is given and never writes to a
database directly.

Field contract: ``additionalProperties: false`` in the canonical schema, so only the exact
fields below are ever emitted. ``actor_id='system'`` is allowed for internal jobs per the
schema description; ``session_id``/``correlation_id`` may be null.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

REQUIRED_FIELDS = (
    "event_id", "timestamp", "event_type", "actor_id", "session_id",
    "action", "resource_type", "result",
)

VALID_ACTIONS = {"create", "read", "update", "delete", "execute",
                 "approve", "reject", "export", "login", "logout"}
VALID_RESULTS = {"success", "error", "denied"}
VALID_CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}


class AuditSink(Protocol):
    def emit(self, event: Dict[str, Any]) -> None: ...


class InMemoryAuditSink:
    """Dev/test sink standing in for audit-service (feature group 17, Character 5).

    Preserves insert order and chains prev_event_hash like the canonical storage rules
    require, so the chain property is testable before the real service exists.
    """

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        self._prev_hash = ""

    def emit(self, event: Dict[str, Any]) -> None:
        event = dict(event)
        event["prev_event_hash"] = self._prev_hash
        # Canonical hash input: the event sans prev_event_hash (documented here, verified
        # by audit-service's integrity job when it lands).
        hashable = {k: v for k, v in event.items() if k != "prev_event_hash"}
        self._prev_hash = hashlib.sha256(
            json.dumps(hashable, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        event["prev_event_hash"] = self._prev_hash
        self.events.append(event)


def build_audit_event(
    *,
    event_type: str,
    actor_id: str,
    action: str,
    resource_type: str,
    result: str,
    resource_id: Optional[str] = None,
    session_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    classification: Optional[str] = None,
    decision: Optional[str] = None,
    error_code: Optional[str] = None,
    reason: Optional[str] = None,
    source_interface: str = "api",
    source_ip: Optional[str] = None,
    payload_hash: Optional[str] = None,
) -> Dict[str, Any]:
    if action not in VALID_ACTIONS:
        raise ValueError(f"audit action {action!r} not in canonical enum")
    if result not in VALID_RESULTS:
        raise ValueError(f"audit result {result!r} not in canonical enum")
    if classification is not None and classification not in VALID_CLASSIFICATIONS:
        raise ValueError(f"classification {classification!r} not in canonical enum")
    if result != "success" and not error_code:
        # Registry rule 3: error_code required if result != 'success'.
        raise ValueError("error_code is required when result != 'success'")

    event: Dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event_type": event_type,
        "actor_id": actor_id,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "task_id": None,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "classification": classification,
        "decision": decision,
        "result": result,
        "error_code": error_code,
        "reason": reason,
        "tool_id": None,
        "model_id": None,
        "artifact_id": None,
        "source_interface": source_interface,
        "source_ip": source_ip,
        "payload_hash": payload_hash,
    }
    return event


def payload_hash(payload: Any) -> str:
    """SHA-256 of the request payload — never the raw payload itself."""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
