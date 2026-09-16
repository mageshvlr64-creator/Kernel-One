"""Cross-service enrichment wiring — industrial-service /internal endpoints.

document-pipeline's side of the Character-3 ingest boundary: upload_validation
calls /internal/resolve-tag + /internal/validate-finding BEFORE persisting,
fail closed, when the payload carries the optional equipment_tag/finding
extensions. Mirrors the evidence-service tests (same contracts), adapted to
this service's OpError/execute() conventions.
"""
from __future__ import annotations

import pytest

from document_pipeline.industrial_gateway import IndustrialGatewayClient
from document_pipeline.ops import OpError

from .conftest import b64, text_payload

UNIT_ID = "aaaaaaaa-0000-0000-0000-000000002000"
PLANT_ID = "aaaaaaaa-0000-0000-0000-000000001000"
EQUIP_ID = "aaaaaaaa-0000-0000-0000-00000000b204"
RESOLUTION = {"tag_number": "P-204", "confidence": "exact_same_unit",
              "matched_equipment_id": EQUIP_ID,
              "requires_human_confirmation": False, "reason": "ok"}
FINDING = {"parameter": "set_pressure", "measured_value": "150 psi",
           "specification": "150 psi", "pass_fail": "PASS"}


def stub_client(responses):
    calls = []

    def opener(method, url, body, headers):
        path = "/" + url.split("/", 3)[3]
        calls.append((method, path, body, headers))
        spec = responses[path]
        if isinstance(spec, Exception):
            raise spec
        return spec

    return IndustrialGatewayClient(opener=opener), calls


class TestUploadEnrichment:
    def test_enriched_upload_persists_document_and_surfaces_resolution(
            self, call, actors, service):
        client, calls = stub_client({
            "/internal/resolve-tag": (200, RESOLUTION),
            "/internal/validate-finding": (200, {"supported": True,
                                                 "ocr_warning": False,
                                                 "fragment": "ok"}),
        })
        service.industrial = client
        payload = text_payload(actors, equipment_tag="P-204",
                               within_unit_id=UNIT_ID, plant_id=PLANT_ID,
                               finding=FINDING)
        result = call(actors["operator"], "upload_validation", payload)
        assert result.status == "ok" and result.state == "UPLOADED"
        got = result.data["industrial_enrichment"]["equipment_resolution"]
        assert got["confidence"] == "exact_same_unit"
        assert got["matched_equipment_id"] == EQUIP_ID
        assert got["requires_human_confirmation"] is False
        assert result.data["industrial_enrichment"]["finding_validation"][
            "supported"] is True
        assert {c[1] for c in calls} == {"/internal/resolve-tag",
                                         "/internal/validate-finding"}
        # A duplicate upload dedups on sha256 WITHOUT calling the dependency.
        calls.clear()
        again = call(actors["operator"], "upload_validation", payload)
        assert again.data.get("deduplicated") is True
        assert calls == []  # dedup short-circuits before enrichment

    def test_plain_upload_never_calls_the_dependency(self, call, actors):
        calls = []

        def opener(method, url, body, headers):  # pragma: no cover — must not fire
            calls.append(url)
            raise AssertionError("dependency must not be called")

        result = call(actors["operator"], "upload_validation", text_payload(actors))
        assert result.status == "ok"
        assert "industrial_enrichment" not in (result.data or {})
        assert calls == []

    def test_dependency_down_fails_closed_with_canonical_error(
            self, call, actors, audit_sink, service):
        client, _ = stub_client({"/internal/resolve-tag": ConnectionError("down")})
        service.industrial = client
        payload = text_payload(actors, equipment_tag="P-204",
                               within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        with pytest.raises(OpError) as err:
            call(actors["operator"], "upload_validation", payload)
        assert err.value.err.code == "DEPENDENCY_UNAVAILABLE"
        # Exactly-one-audit-event invariant holds on the failure path too.
        events = [e for e in audit_sink.events
                  if e.get("event_type") == "document_ingestion.upload_validation"]
        assert len(events) == 1 and events[0]["result"] == "error"

    def test_non_2xx_fails_closed(self, call, actors, service):
        client, _ = stub_client({"/internal/resolve-tag": (503, {"detail": "x"})})
        service.industrial = client
        payload = text_payload(actors, equipment_tag="P-204",
                               within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        with pytest.raises(OpError) as err:
            call(actors["operator"], "upload_validation", payload)
        assert err.value.err.code == "DEPENDENCY_UNAVAILABLE"

    def test_403_from_dependency_maps_to_policy_denied(self, call, actors,
                                                       service):
        client, _ = stub_client({"/internal/resolve-tag": (403, {"detail": "no"})})
        service.industrial = client
        payload = text_payload(actors, equipment_tag="P-204",
                               within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        with pytest.raises(OpError) as err:
            call(actors["operator"], "upload_validation", payload)
        assert err.value.err.code == "POLICY_DENIED"

    def test_bad_extension_shape_is_invalid_request_without_dependency_call(
            self, call, actors):
        client, calls = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        payload = text_payload(actors, equipment_tag="  ",
                               within_unit_id="not-a-uuid", plant_id=PLANT_ID)
        with pytest.raises(OpError) as err:
            call(actors["operator"], "upload_validation", payload)
        assert err.value.err.code == "INVALID_REQUEST"
        assert calls == []

    def test_enrichment_failure_persists_no_document(self, call, actors, service):
        client, _ = stub_client({"/internal/resolve-tag": ConnectionError("x")})
        service.industrial = client
        payload = text_payload(actors, equipment_tag="P-204",
                               within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        with pytest.raises(OpError):
            call(actors["operator"], "upload_validation", payload)
        ws = actors["operator"].workspace_id
        assert service.store.list_by_workspace(ws) == []


class TestGatewayClient:
    def test_roles_header_and_body_contract(self):
        client, calls = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        got = client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                                 plant_id=PLANT_ID)
        assert got == RESOLUTION
        method, path, body, headers = calls[0]
        assert (method, path) == ("POST", "/internal/resolve-tag")
        assert body == {"tag_number": "P-204", "within_unit_id": UNIT_ID,
                        "plant_id": PLANT_ID}
        assert headers["X-Roles"] == "Equipment:read"

    def test_http_403_path_translates(self, monkeypatch):
        import urllib.error

        class _Resp:
            def read(self):
                return b'{"detail": "forbidden"}'

            def close(self):
                pass

        def fake_urlopen(req, timeout=None):  # noqa: ARG001
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden",
                                         hdrs=None, fp=_Resp())

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        client = IndustrialGatewayClient(base_url="http://127.0.0.1:1")
        with pytest.raises(Exception) as err:
            client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                               plant_id=PLANT_ID)
        assert getattr(err.value, "code", "") == "POLICY_DENIED" \
            or getattr(getattr(err.value, "err", None), "code", "") \
            == "POLICY_DENIED"
