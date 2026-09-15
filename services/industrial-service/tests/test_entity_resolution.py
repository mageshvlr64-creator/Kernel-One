"""
Unit tests for entity resolution.

Tests the three-case logic from docs/industrial/13_asset_knowledge_graph.md.

These tests use mock repositories rather than a real database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.entity_resolution import EntityResolver
from app.models import Equipment, EquipmentStatus


def _make_equipment(unit_id: uuid.UUID, tag: str) -> Equipment:
    return Equipment(
        id=uuid.uuid4(),
        unit_id=unit_id,
        tag_number=tag,
        name=f"Equipment {tag}",
        status=EquipmentStatus.operational,
        created_at=datetime.now(timezone.utc),
    )


UNIT_A = uuid.uuid4()
UNIT_B = uuid.uuid4()
PLANT_ID = uuid.uuid4()


@pytest.fixture
def mock_equipment_repo():
    repo = MagicMock()
    repo.find_by_tag_in_unit = AsyncMock(return_value=None)
    repo.find_by_tag_in_plant = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_graph_repo():
    repo = MagicMock()
    repo.add_governing_document = AsyncMock()
    return repo


@pytest.fixture
def resolver(mock_equipment_repo, mock_graph_repo):
    return EntityResolver(mock_equipment_repo, mock_graph_repo)


class TestEntityResolution:
    @pytest.mark.asyncio
    async def test_case1_exact_same_unit(self, resolver, mock_equipment_repo):
        """Case 1: exact match within the same unit — auto-linked, no human confirmation."""
        equipment = _make_equipment(UNIT_A, "P-204")
        mock_equipment_repo.find_by_tag_in_unit.return_value = equipment

        result = await resolver.resolve("P-204", UNIT_A, PLANT_ID)

        assert result.confidence == "exact_same_unit"
        assert result.matched_equipment_id == equipment.id
        assert result.requires_human_confirmation is False

    @pytest.mark.asyncio
    async def test_case2_cross_unit_requires_confirmation(
        self, resolver, mock_equipment_repo
    ):
        """Case 2: match in different unit — requires human confirmation before linking."""
        equipment = _make_equipment(UNIT_B, "P-204")
        mock_equipment_repo.find_by_tag_in_unit.return_value = None
        mock_equipment_repo.find_by_tag_in_plant.return_value = [equipment]

        result = await resolver.resolve("P-204", UNIT_A, PLANT_ID)

        assert result.confidence == "exact_other_unit"
        assert result.matched_equipment_id == equipment.id
        assert result.requires_human_confirmation is True

    @pytest.mark.asyncio
    async def test_case2_returns_all_candidates(self, resolver, mock_equipment_repo):
        """Case 2 with reused tags: every match is returned for the human UI."""
        eq_b = _make_equipment(UNIT_B, "P-204")
        eq_c = _make_equipment(uuid.uuid4(), "P-204")
        mock_equipment_repo.find_by_tag_in_unit.return_value = None
        mock_equipment_repo.find_by_tag_in_plant.return_value = [eq_b, eq_c]

        result = await resolver.resolve("P-204", UNIT_A, PLANT_ID)

        assert result.candidate_equipment_ids == [eq_b.id, eq_c.id]
        assert result.matched_equipment_id == eq_b.id

    @pytest.mark.asyncio
    async def test_case3_no_match(self, resolver, mock_equipment_repo):
        """Case 3: no match — document still ingested but has no equipment_id link."""
        mock_equipment_repo.find_by_tag_in_unit.return_value = None
        mock_equipment_repo.find_by_tag_in_plant.return_value = []

        result = await resolver.resolve("P-204", UNIT_A, PLANT_ID)

        assert result.confidence == "no_match"
        assert result.matched_equipment_id is None
        assert result.requires_human_confirmation is False

    @pytest.mark.asyncio
    async def test_confirm_and_link_calls_graph_repo(self, resolver, mock_graph_repo):
        """Confirming a link should persist the governed_by edge."""
        equipment_id = uuid.uuid4()
        document_id = uuid.uuid4()

        await resolver.confirm_and_link(
            equipment_id, document_id, "operating procedure"
        )

        mock_graph_repo.add_governing_document.assert_called_once_with(
            equipment_id=equipment_id,
            document_id=document_id,
            relationship_note="operating procedure",
        )
