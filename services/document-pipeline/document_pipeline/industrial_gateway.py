"""Cross-service enrichment client — industrial-service /internal endpoints.

document-pipeline's copy of the enrichment client (DEC-023: services don't
import each other's code; the same small client lives in each caller). This is
the Character-3 ingest wiring named in the industrial-service changelog:
`upload_validation` calls `/internal/resolve-tag` + `/internal/validate-finding`
BEFORE the Document row is persisted, when the upload payload carries the
optional `equipment_tag` (+ `within_unit_id`, `plant_id`) / `finding` extensions.

Differences from evidence-service's copy:
- raises bare `RegistryError`; execute() is the single place that wraps
  failures into OpError with the correlation/audit ids (exactly-one-audit-event
  invariant), so the HTTP layer behaves exactly as for any other op failure.
- runs under the document-processing retry class via the caller (the op layer
  wraps the enrichment call in run_with_retry).

Contract facts (verified against services/industrial-service/app/main.py):
- Auth: `X-Roles: Equipment:read` required on both endpoints; dev stub accepts
  it verbatim; a 403 from the dependency maps to POLICY_DENIED.
- resolve-tag: {tag_number, within_unit_id, plant_id} -> EntityResolutionResult.
  Case-2 (ambiguous) results are surfaced for human confirmation — this
  service never persists governed_by edges.
- validate-finding: Finding fields -> {supported, ocr_warning, fragment};
  flags surfaced, never gated.
- Failure posture: fail closed. Transport failures, timeouts, and non-2xx
  responses raise DEPENDENCY_UNAVAILABLE (retryable, document-processing
  class), so a dependency outage never persists an unenriched Document.

The transport is injectable (`opener`) so tests stub HTTP without sockets; the
production path is stdlib urllib per the DEC-023 no-framework posture.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

from .errors import RegistryError

DEFAULT_BASE_URL = "http://127.0.0.1:8005"
DEFAULT_TIMEOUT_SECONDS = 5.0

# Both /internal endpoints consumed here sit behind Equipment:read.
REQUIRED_ROLES = "Equipment:read"

# Test seam: (method, url, body_dict, headers_dict) -> (status, parsed_json).
Opener = Callable[[str, str, Dict[str, Any], Dict[str, str]], Any]


def _invalid(details, operator_detail: str) -> RegistryError:
    """Build the INVALID_REQUEST failure for malformed extension shapes."""
    return RegistryError("INVALID_REQUEST", details=details,
                         operator_detail=operator_detail)


class IndustrialGatewayClient:
    """Client for the industrial-service /internal resolve-tag and
    validate-finding endpoints used during document-pipeline ingest."""

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

    def enrich(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Enrich an upload payload; None when no extension keys are present.

        Validation of the extension shapes happens here too (INVALID_REQUEST,
        no dependency call), so the op layer stays thin.
        """
        tag = payload.get("equipment_tag")
        unit = payload.get("within_unit_id")
        plant = payload.get("plant_id")
        finding = payload.get("finding")
        if tag is None and finding is None:
            return None
        out: Dict[str, Any] = {}
        if tag is not None:
            if not isinstance(tag, str) or not tag.strip() \
                    or not _is_uuid(unit) or not _is_uuid(plant):
                raise _invalid(
                    [{"field": "equipment_tag",
                      "issue": "required non-empty string"},
                     {"field": "within_unit_id/plant_id",
                      "issue": "required uuids when equipment_tag is present"}],
                    "industrial enrichment requires equipment_tag with "
                    "within_unit_id and plant_id")
            out["equipment_resolution"] = self.resolve_tag(
                tag_number=tag.strip(), within_unit_id=unit, plant_id=plant)
        if finding is not None:
            if not isinstance(finding, dict):
                raise _invalid([{"field": "finding", "issue": "must be an object"}],
                               "finding enrichment requires a JSON object")
            out["finding_validation"] = self.validate_finding(finding)
        return out

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
                   headers: Dict[str, str]) -> Tuple[int, Any]:
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


def _is_uuid(value: Any) -> bool:
    import uuid as _uuid
    if not isinstance(value, str):
        return False
    try:
        _uuid.UUID(value)
    except ValueError:
        return False
    return True


def _safe_json(raw: bytes) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
