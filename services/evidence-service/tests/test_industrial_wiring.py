"""Cross-service enrichment wiring — industrial-service /internal endpoints.

Covers the Character-3 side of the boundary named in the industrial-service
changelog ("call /internal/validate-finding + /internal/resolve-tag from
ingest"): op 01 (evidence_system) enriches BEFORE persisting, fail closed.
The gateway client is exercised through its injectable transport seam (no
sockets); one HTTP-level test covers the production urllib path end to end.
"""
from __future__ import annotations

import uuid

import pytest

from evidence_service.errors import RegistryError
from evidence_service.industrial_gateway import IndustrialGatewayClient

from tests.conftest import (TASK_ID, create_evidence, make_actor)


def stub_client(responses):
    """Build a client whose transport returns canned (status, payload) pairs.

    `responses` maps path -> (status, payload) or path -> Exception.
    Calls are recorded as (method, path, body, headers) tuples.
    """
    calls = []

    def opener(method, url, body, headers):
        path = "/" + url.split("/", 3)[-1] if url.count("/") > 3 else url
        # url looks like http://host:port/internal/resolve-tag — take from
        # the first path segment after the origin.
        path = "/" + url.split("/", 3)[3]
        calls.append((method, path, body, headers))
        spec = responses[path]
        if isinstance(spec, Exception):
            raise spec
        return spec

    return IndustrialGatewayClient(opener=opener), calls


UNIT_ID = "44444444-4444-4444-8444-444444444444"
PLANT_ID = "55555555-5555-5555-8555-555555555555"
RESOLUTION = {"tag_number": "P-204", "confidence": "exact_same_unit",
              "matched_equipment_id": str(uuid.uuid4()),
              "requires_human_confirmation": False, "reason": "exact match"}
FINDING = {"parameter": "set_pressure", "measured_value": "150 psi",
           "specification": "150 psi", "pass_fail": "PASS"}


# --------------------------------------------------------------- client unit

class TestGatewayClient:
    def test_resolve_tag_sends_roles_header_and_body(self):
        client, calls = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        got = client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                                 plant_id=PLANT_ID)
        assert got == RESOLUTION
        method, path, body, headers = calls[0]
        assert (method, path) == ("POST", "/internal/resolve-tag")
        assert body == {"tag_number": "P-204", "within_unit_id": UNIT_ID,
                        "plant_id": PLANT_ID}
        assert headers["X-Roles"] == "Equipment:read"

    def test_validate_finding_round_trip(self):
        client, calls = stub_client({"/internal/validate-finding": (
            200, {"supported": True, "ocr_warning": False,
                  "fragment": "150 psi (PASS)"})})
        got = client.validate_finding(FINDING)
        assert got["supported"] is True and got["fragment"]
        assert calls[0][1] == "/internal/validate-finding"

    def test_dependency_down_raises_canonical_error(self):
        client, _ = stub_client({"/internal/resolve-tag": (
            ConnectionError("refused"))})
        with pytest.raises(RegistryError) as err:
            client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                               plant_id=PLANT_ID)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"

    @pytest.mark.parametrize("status", [404, 500, 503])
    def test_non_2xx_fails_closed(self, status):
        client, _ = stub_client({"/internal/resolve-tag": (status, {"detail": "x"})})
        with pytest.raises(RegistryError) as err:
            client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                               plant_id=PLANT_ID)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"

    def test_403_translates_to_policy_denied(self):
        client, _ = stub_client({"/internal/resolve-tag": (403, {"detail": "no"})})
        with pytest.raises(RegistryError) as err:
            client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                               plant_id=PLANT_ID)
        assert err.value.code == "POLICY_DENIED"

    def test_timeout_fails_closed(self):
        client, _ = stub_client({"/internal/validate-finding": TimeoutError("t")})
        with pytest.raises(RegistryError) as err:
            client.validate_finding(FINDING)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"


# ------------------------------------------------------- op-01 wiring (ingest)

class TestIngestWiring:
    def test_payload_without_extensions_never_calls_dependency(self, service):
        calls = []

        def opener(method, url, body, headers):  # pragma: no cover — must not fire
            calls.append(url)
            raise AssertionError("dependency must not be called")

        service.industrial = IndustrialGatewayClient(opener=opener)
        result = create_evidence(service, make_actor("Operator"))
        assert "industrial_enrichment" not in result.data
        assert calls == []

    def test_ingest_with_tag_and_finding_persists_enriched_row(self, service):
        client, calls = stub_client({
            "/internal/resolve-tag": (200, RESOLUTION),
            "/internal/validate-finding": (200, {"supported": True,
                                                 "ocr_warning": False,
                                                 "fragment": "ok"}),
        })
        service.industrial = client
        result = create_evidence(
            service, make_actor("Operator"),
            equipment_tag="P-204", within_unit_id=UNIT_ID, plant_id=PLANT_ID,
            finding=FINDING)
        data = result.data
        assert data["industrial_enrichment"]["equipment_resolution"] == RESOLUTION
        assert data["industrial_enrichment"]["finding_validation"]["supported"] is True
        # The row is persisted with the base fields untouched by enrichment.
        ev = service.links.get(data["evidence_id"])
        assert ev is not None and ev.task_id == TASK_ID
        assert {c[1] for c in calls} == {"/internal/resolve-tag",
                                         "/internal/validate-finding"}

    def test_ingest_with_tag_only_calls_resolve_tag_once(self, service):
        client, calls = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        service.industrial = client
        result = create_evidence(service, make_actor("Operator"),
                                 equipment_tag="P-204",
                                 within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        assert "finding_validation" not in result.data["industrial_enrichment"]
        assert [c[1] for c in calls] == ["/internal/resolve-tag"]

    def test_ambiguous_resolution_is_surfaced_not_gated(self, service):
        case2 = dict(RESOLUTION, confidence="same_unit_different_name",
                     requires_human_confirmation=True)
        client, _ = stub_client({"/internal/resolve-tag": (200, case2)})
        service.industrial = client
        result = create_evidence(service, make_actor("Operator"),
                                 equipment_tag="P-204",
                                 within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        got = result.data["industrial_enrichment"]["equipment_resolution"]
        assert got["requires_human_confirmation"] is True
        # The Evidence row still exists (human confirmation is downstream's job).
        assert service.links.get(result.data["evidence_id"]) is not None

    def test_dependency_failure_persists_nothing_and_fails_closed(self, service):
        client, _ = stub_client({"/internal/resolve-tag": ConnectionError("down")})
        service.industrial = client
        with pytest.raises(RegistryError) as err:
            create_evidence(service, make_actor("Operator"),
                            equipment_tag="P-204",
                            within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"
        # Fail closed: no Evidence row for the task.
        assert service.links.for_task(TASK_ID) == []

    def test_dependency_failure_is_retried_under_canonical_policy(self, service):
        # DEPENDENCY_UNAVAILABLE is in run_with_retry's retryable set (runtime/11
        # interactive-read class): one transient failure then success must pass.
        import inspect

        from evidence_service import retry
        assert "DEPENDENCY_UNAVAILABLE" in set(
            inspect.signature(retry.run_with_retry)
            .parameters["retryable"].default)
        attempts = {"n": 0}

        def flaky(method, url, body, headers):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise ConnectionError("transient")
            return 200, RESOLUTION

        service.industrial = IndustrialGatewayClient(opener=flaky)
        result = create_evidence(service, make_actor("Operator"),
                                 equipment_tag="P-204",
                                 within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        assert attempts["n"] == 2
        assert result.data["industrial_enrichment"]["equipment_resolution"] \
            == RESOLUTION

    def test_validation_failure_persists_nothing(self, service):
        client, _ = stub_client({"/internal/validate-finding": (500, {"d": 1})})
        service.industrial = client
        with pytest.raises(RegistryError) as err:
            create_evidence(service, make_actor("Operator"), finding=FINDING)
        assert err.value.code == "DEPENDENCY_UNAVAILABLE"
        assert service.links.for_task(TASK_ID) == []

    def test_bad_tag_payload_is_invalid_request_without_calling_dependency(self,
                                                                           service):
        client, calls = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        service.industrial = client
        with pytest.raises(RegistryError) as err:
            create_evidence(service, make_actor("Operator"),
                            equipment_tag="  ", within_unit_id="not-a-uuid",
                            plant_id=PLANT_ID)
        assert err.value.code == "INVALID_REQUEST"
        assert calls == []

    def test_exactly_one_audit_event_per_ingest(self, service):
        client, _ = stub_client({"/internal/resolve-tag": (200, RESOLUTION)})
        service.industrial = client
        result = create_evidence(service, make_actor("Operator"),
                                 equipment_tag="P-204",
                                 within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        events = [e for e in service.audit_sink.events
                  if e["event_id"] == result.audit_event_id]
        assert len(events) == 1
        assert events[0]["event_type"] == "evidence_and_provenance.evidence_system"

    def test_failed_ingest_still_audits_once_as_error(self, service):
        client, _ = stub_client({"/internal/resolve-tag": ConnectionError("x")})
        service.industrial = client
        with pytest.raises(RegistryError):
            create_evidence(service, make_actor("Operator"),
                            equipment_tag="P-204",
                            within_unit_id=UNIT_ID, plant_id=PLANT_ID)
        events = [e for e in service.audit_sink.events
                  if e["event_type"] == "evidence_and_provenance.evidence_system"]
        assert len(events) == 1 and events[0]["result"] == "error"
        assert events[0]["error_code"] == "DEPENDENCY_UNAVAILABLE"


# ------------------------------------------------- HTTP-level client behavior

class TestGatewayHttpPath:
    def test_http_error_status_fails_closed(self):
        """Production transport: an HTTPError must map to the canonical code."""
        import urllib.error

        class _Resp:
            def read(self):
                return b'{"detail": "forbidden"}'

            def close(self):
                pass

        original = urllib.request.urlopen

        def fake_urlopen(req, timeout=None):  # noqa: ARG001
            raise urllib.error.HTTPError(req.full_url, 403, "Forbidden",
                                         hdrs=None, fp=_Resp())

        urllib.request.urlopen = fake_urlopen
        try:
            client = IndustrialGatewayClient(base_url="http://127.0.0.1:1")
            with pytest.raises(RegistryError) as err:
                client.resolve_tag(tag_number="P-204", within_unit_id=UNIT_ID,
                                   plant_id=PLANT_ID)
            assert err.value.code == "POLICY_DENIED"
        finally:
            urllib.request.urlopen = original
