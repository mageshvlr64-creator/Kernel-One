"""Cross-service enrichment client — industrial-service /internal endpoints.

Implements the Character-3 side of the wiring boundary named in the
industrial-service changelog ("call /internal/validate-finding +
/internal/resolve-tag from ingest"): evidence-service ingest (op 01,
`evidence_system`) calls both endpoints before persisting an Evidence row when
the ingest payload carries the optional `equipment_tag` / `finding` extensions.

Contract facts (verified against services/industrial-service/app/main.py):
- Auth: `X-Roles: Equipment:read` is required on both endpoints (permission
  matrix, docs/reference/05_permission_matrix.md); the dev stub accepts it
  verbatim. No bearer token is exchanged between services.
- resolve-tag request: {tag_number, within_unit_id, plant_id} (all required).
  Response (EntityResolutionResult): {tag_number, confidence,
  matched_equipment_id, requires_human_confirmation, reason}. Case-2
  (ambiguous) results are SURFACED for human confirmation — evidence-service
  never persists governed_by edges itself (that is /internal/confirm-link's
  job, after a human approves).
- validate-finding request: Finding fields (parameter required;
  measured_value, specification, pass_fail, location_reference,
  evidence_id_*, ocr_confidence optional). Response: {supported, ocr_warning,
  fragment}. Flags are surfaced, never gated — the caller decides.
- Failure posture: fail closed. Transport failures, timeouts, and non-2xx
  responses raise DEPENDENCY_UNAVAILABLE (canonical registry; retryable under
  the runtime/11 interactive-read class) so ingest never persists an
  unenriched row silently. A 403 from the dependency means our own role
  header was rejected — translated to POLICY_DENIED, which is not retried.

The transport is injectable (`opener`) so tests stub HTTP without sockets;
the production path is stdlib urllib per the DEC-023 no-framework posture.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

from .errors import RegistryError

DEFAULT_BASE_URL = "http://127.0.0.1:8005"
DEFAULT_TIMEOUT_SECONDS = 5.0

# Both /internal endpoints consumed here sit behind Equipment:read.
REQUIRED_ROLES = "Equipment:read"

# Test seam: (method, url, body_dict, headers_dict) -> (status, parsed_json).
Opener = Callable[[str, str, Dict[str, Any], Dict[str, str]], Any]


class IndustrialGatewayClient:
    """Client for the industrial-service /internal resolve-tag and
    validate-finding endpoints used during evidence ingest."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL,
                 timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
                 roles_header: str = REQUIRED_ROLES,
                 opener: Optional[Opener] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.roles_header = roles_header
        self._opener = opener

    # ------------------------------------------------------------------ API
    def resolve_tag(self, *, tag_number: str, within_unit_id: str,
                    plant_id: str) -> Dict[str, Any]:
        """POST /internal/resolve-tag — entity resolution for one extracted tag."""
        body = {"tag_number": tag_number,
                "within_unit_id": str(within_unit_id),
                "plant_id": str(plant_id)}
        return self._post("/internal/resolve-tag", body)

    def validate_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """POST /internal/validate-finding — inspection-finding validation."""
        return self._post("/internal/validate-finding", finding)

    # -------------------------------------------------------------- internals
    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"X-Roles": self.roles_header}
        try:
            if self._opener is not None:
                raw = self._opener("POST", self.base_url + path, body, headers)
            else:
                raw = self._post_http(path, body, headers)
            status, payload = raw
        except RegistryError:
            raise
        except Exception as exc:  # noqa: BLE001 — translated below, fail closed
            raise RegistryError(
                "DEPENDENCY_UNAVAILABLE",
                operator_detail=f"industrial-service {path} unreachable: "
                                f"{type(exc).__name__}: {exc}") from exc
        if status == 403:
            raise RegistryError(
                "POLICY_DENIED",
                operator_detail=f"industrial-service {path} rejected the "
                                f"{self.roles_header} role header")
        if not 200 <= status < 300 or not isinstance(payload, dict):
            raise RegistryError(
                "DEPENDENCY_UNAVAILABLE",
                operator_detail=f"industrial-service {path} returned HTTP "
                                f"{status}" + ("" if isinstance(payload, dict)
                                               else " with a non-object body"))
        return payload

    def _post_http(self, path: str, body: Dict[str, Any],
                   headers: Dict[str, str]) -> Any:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path, data=data, method="POST",
            headers={**headers, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, _safe_json(err.read())
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise RegistryError(
                "DEPENDENCY_UNAVAILABLE",
                operator_detail=f"industrial-service {path} unreachable: "
                                f"{err}") from err


def _safe_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
