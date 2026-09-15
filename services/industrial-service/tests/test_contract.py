"""
Contract tests: the service's public surface, pinned against accidental loss.

Lesson: an edit once silently deleted a repository method and its route kept
calling it — unit tests with mocks did not catch it. These tests assert the
route inventory, repository method surface, and cross-module invariants
directly, so deletions fail loudly.
"""

from __future__ import annotations

from app import main
from app import database as db
from app.comparison import LOW_CONFIDENCE_THRESHOLD, SYNONYM_MAP, TABLE_CONFIDENCE_CAP
from app.inspection_logic import VALID_ANSWER_KINDS
from app.models import ConflictResolutionKind


def _routes():
    paths = set()
    for route in main.app.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", "")
        for method in methods:
            paths.add((method, path))
    return paths


EXPECTED_ROUTES = {
    ("POST", "/plants"),
    ("GET", "/plants/{plant_id}"),
    ("GET", "/organizations/{org_id}/plants"),
    ("POST", "/units"),
    ("GET", "/units/{unit_id}"),
    ("GET", "/plants/{plant_id}/units"),
    ("GET", "/assets"),
    ("GET", "/assets/table"),
    ("POST", "/units/{unit_id}/equipment"),
    ("GET", "/assets/{equipment_id}"),
    ("PATCH", "/assets/{equipment_id}"),
    ("DELETE", "/assets/{equipment_id}"),
    ("POST", "/assets/{equipment_id}/maintenance-events"),
    ("GET", "/assets/{equipment_id}/maintenance-events"),
    ("POST", "/assets/{equipment_id}/inspections"),
    ("GET", "/assets/{equipment_id}/inspections"),
    ("POST", "/assets/{equipment_id}/incidents"),
    ("GET", "/assets/{equipment_id}/incidents"),
    ("POST", "/assets/{equipment_id}/governing-documents"),
    ("GET", "/assets/{equipment_id}/governing-documents"),
    ("DELETE", "/assets/{equipment_id}/governing-documents/{document_id}"),
    ("POST", "/internal/resolve-tag"),
    ("POST", "/internal/confirm-link"),
    ("POST", "/internal/detect-conflicts"),
    ("POST", "/internal/compare-documents"),
    ("POST", "/internal/validate-finding"),
    ("POST", "/internal/validate-answer"),
    ("POST", "/internal/verify-calculation"),
    ("POST", "/internal/check-sop-compliance"),
    ("GET", "/assets/{equipment_id}/detail"),
    ("GET", "/documents/{document_id}/equipment"),
    ("POST", "/assets/{equipment_id}/conflicts/resolve"),
    ("GET", "/assets/{equipment_id}/conflict-resolutions"),
    ("GET", "/healthz"),
}


class TestRouteInventory:
    def test_all_expected_routes_registered(self):
        missing = EXPECTED_ROUTES - _routes()
        assert not missing, f"routes lost: {missing}"


class TestRepositorySurface:
    def test_equipment_repository_methods(self):
        for name in (
            "create",
            "get",
            "list_by_unit",
            "search",
            "search_with_history",
            "update",
            "soft_delete",
            "find_by_tag_in_unit",
            "find_by_tag_in_plant",
        ):
            assert callable(getattr(db.EquipmentRepository, name, None)), name

    def test_history_repository_methods(self):
        for cls in (
            db.MaintenanceEventRepository,
            db.InspectionRepository,
            db.IncidentRepository,
        ):
            assert callable(getattr(cls, "create", None))
            assert callable(getattr(cls, "list_by_equipment", None))

    def test_graph_and_resolution_methods(self):
        for name in (
            "add_governing_document",
            "remove_governing_document",
            "get_governing_documents",
            "get_equipment_for_document",
            "get_shared_equipment_for_documents",
        ):
            assert callable(getattr(db.KnowledgeGraphRepository, name, None)), name
        assert callable(db.ConflictResolutionRepository.record)
        assert callable(db.ConflictResolutionRepository.list_by_equipment)


class TestCrossModuleInvariants:
    def test_answer_kinds_complete(self):
        assert set(VALID_ANSWER_KINDS) == {
            "sop",
            "calculation",
            "drawing",
            "pid",
            "general",
        }

    def test_resolution_kinds_complete(self):
        assert {k.value for k in ConflictResolutionKind} == {
            "downgrade_authority",
            "set_effective_until",
            "acknowledge_both",
        }

    def test_table_cap_flags_low_confidence(self):
        """A table-capped entry must trip the low-confidence flag downstream."""
        assert TABLE_CONFIDENCE_CAP < LOW_CONFIDENCE_THRESHOLD

    def test_synonym_table_nonempty(self):
        assert len(SYNONYM_MAP) > 0

    def test_db_pool_uninitialised_fails_closed(self):
        import pytest

        main._pool = None
        with pytest.raises(RuntimeError):
            main.get_db_pool()

    def test_db_pool_success_and_resolver_factory(self):
        from unittest.mock import MagicMock

        from app.entity_resolution import EntityResolver

        sentinel = object()
        main._pool = sentinel
        try:
            assert main.get_db_pool() is sentinel
        finally:
            main._pool = None
        resolver = main.entity_resolver(MagicMock(), MagicMock())
        assert isinstance(resolver, EntityResolver)


class TestDiFactories:
    def test_factories_return_repositories(self):
        import sys

        sys.path.insert(0, ".")
        from tests.test_database import FakeConn, FakePool

        pool = FakePool(FakeConn())
        assert isinstance(main.equipment_repo(pool), db.EquipmentRepository)
        assert isinstance(main.plant_repo(pool), db.PlantRepository)
        assert isinstance(main.unit_repo(pool), db.UnitRepository)
        assert isinstance(main.maintenance_repo(pool), db.MaintenanceEventRepository)
        assert isinstance(main.inspection_repo(pool), db.InspectionRepository)
        assert isinstance(main.incident_repo(pool), db.IncidentRepository)
        assert isinstance(main.graph_repo(pool), db.KnowledgeGraphRepository)
        assert isinstance(
            main.conflict_resolution_repo(pool), db.ConflictResolutionRepository
        )
