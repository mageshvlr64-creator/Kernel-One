"""
Entity Resolution for the Industrial Knowledge Graph.

Implements the three-case tag-matching logic from:
  docs/industrial/13_asset_knowledge_graph.md — "Entity resolution" section

This module is called by the document-ingestion webhook handler whenever a
document mentions an equipment tag (e.g. "P-204").  It deliberately does NOT
auto-commit a link in the ambiguous case — it returns a result that the caller
must then surface to a human for confirmation (case 2) or skip (case 3).
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.database import EquipmentRepository, KnowledgeGraphRepository
from app.models import EntityResolutionResult


class EntityResolver:
    """Resolves a raw equipment tag string to an Equipment row.

    Per docs/industrial/13_asset_knowledge_graph.md:

    Case 1 — Exact tag match within the same Unit:
        Highest confidence.  Auto-linked without human confirmation.

    Case 2 — Exact tag match in a different Unit of the same Plant:
        Tag numbers are sometimes reused across units, so this requires
        human confirmation before the link is persisted.

    Case 3 — No match:
        The document is still usable for Q&A via the knowledge fabric;
        it simply has no equipment_id link until a human creates the Equipment
        row or links manually via ui/23_asset_view.md.
    """

    def __init__(
        self,
        equipment_repo: EquipmentRepository,
        graph_repo: KnowledgeGraphRepository,
    ) -> None:
        self._equipment_repo = equipment_repo
        self._graph_repo = graph_repo

    async def resolve(
        self,
        tag_number: str,
        within_unit_id: uuid.UUID,
        plant_id: uuid.UUID,
    ) -> EntityResolutionResult:
        """Attempt to match *tag_number* to an Equipment row.

        Args:
            tag_number:      Raw tag string extracted from the document, e.g. "P-204".
            within_unit_id:  The Unit the ingested document is scoped to.
            plant_id:        The Plant that Unit belongs to (for cross-unit search).

        Returns:
            EntityResolutionResult with confidence level and matched id (or None).
        """
        # Case 1 — exact match in the target unit
        match_same_unit = await self._equipment_repo.find_by_tag_in_unit(
            tag_number=tag_number, unit_id=within_unit_id
        )
        if match_same_unit:
            return EntityResolutionResult(
                tag_number=tag_number,
                confidence="exact_same_unit",
                matched_equipment_id=match_same_unit.id,
                matched_unit_id=match_same_unit.unit_id,
                requires_human_confirmation=False,
                reason=(
                    f"Exact tag match found in the target unit "
                    f"(equipment id={match_same_unit.id})."
                ),
            )

        # Case 2 — exact match in a different unit of the same plant
        cross_unit_matches = await self._equipment_repo.find_by_tag_in_plant(
            tag_number=tag_number,
            plant_id=plant_id,
            exclude_unit_id=within_unit_id,
        )
        if cross_unit_matches:
            # Return ALL candidates — the human confirmation UI shows every
            # match since tag numbers are sometimes reused across units.
            first = cross_unit_matches[0]
            return EntityResolutionResult(
                tag_number=tag_number,
                confidence="exact_other_unit",
                matched_equipment_id=first.id,
                matched_unit_id=first.unit_id,
                candidate_equipment_ids=[m.id for m in cross_unit_matches],
                requires_human_confirmation=True,
                reason=(
                    f"Tag '{tag_number}' matched {len(cross_unit_matches)} "
                    f"equipment row(s) in other units of the plant "
                    f"(first: unit_id={first.unit_id}).  Tag numbers are sometimes "
                    f"reused across units — human confirmation required before "
                    f"auto-linking."
                ),
            )

        # Case 3 — no match
        return EntityResolutionResult(
            tag_number=tag_number,
            confidence="no_match",
            matched_equipment_id=None,
            matched_unit_id=None,
            requires_human_confirmation=False,
            reason=(
                f"No Equipment row found for tag '{tag_number}' in plant "
                f"(plant_id={plant_id}).  Document can still be ingested and "
                f"retrieved normally; it has no equipment_id link until a human "
                f"creates the matching Equipment row or manually links it."
            ),
        )

    async def confirm_and_link(
        self,
        equipment_id: uuid.UUID,
        document_id: uuid.UUID,
        relationship_note: Optional[str] = None,
    ) -> None:
        """Persist a governed_by edge after human confirmation.

        Called by the API when a user explicitly approves a case-2 match or
        manually links a document via ui/23_asset_view.md.
        """
        await self._graph_repo.add_governing_document(
            equipment_id=equipment_id,
            document_id=document_id,
            relationship_note=relationship_note,
        )
