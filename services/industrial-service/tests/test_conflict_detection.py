"""
Unit tests for knowledge conflict detection.

Tests are written against docs/industrial/14_knowledge_conflict_detection.md.

Run with: pytest services/industrial-service/tests/
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.conflict_detection import (
    _dates_overlap,
    detect_conflicts,
    format_conflict_output,
)
from app.models import ConflictRecord


EQUIPMENT_ID = uuid.uuid4()
DOC_A_ID = uuid.uuid4()
DOC_B_ID = uuid.uuid4()


def _claim(
    document_id,
    document_name,
    authority,
    parameter,
    value,
    effective_from=None,
    effective_until=None,
):
    return {
        "document_id": document_id,
        "document_name": document_name,
        "authority": authority,
        "parameter": parameter,
        "value": value,
        "effective_from": effective_from,
        "effective_until": effective_until,
    }


# ---------------------------------------------------------------------------
# _dates_overlap helper
# ---------------------------------------------------------------------------


class TestDatesOverlap:
    def test_overlapping_windows_returns_true(self):
        assert (
            _dates_overlap(
                date(2022, 1, 1),
                date(2024, 1, 1),
                date(2023, 6, 1),
                None,
            )
            is True
        )

    def test_non_overlapping_windows_returns_false(self):
        # A ended in 2021, B started in 2022
        assert (
            _dates_overlap(
                date(2020, 1, 1),
                date(2021, 12, 31),
                date(2022, 1, 1),
                None,
            )
            is False
        )

    def test_both_open_ended_overlap(self):
        assert _dates_overlap(None, None, None, None) is True

    def test_one_open_ended_overlaps_with_active(self):
        assert (
            _dates_overlap(
                date(2023, 1, 1),
                None,
                date(2024, 1, 1),
                None,
            )
            is True
        )


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------


class TestDetectConflicts:
    def test_no_conflict_when_values_agree(self):
        claims = [
            _claim(
                DOC_A_ID,
                "SOP-204",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 1, 1),
            ),
            _claim(
                DOC_B_ID,
                "SOP-205",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 1, 1),
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert conflicts == []

    def test_genuine_conflict_detected_and_unresolved(self):
        """
        Both documents are primary authority, currently effective, and disagree.
        Per docs/industrial/14_knowledge_conflict_detection.md step 5:
        "this is a genuine, unresolved conflict. It is surfaced, never auto-resolved."
        """
        claims = [
            _claim(
                DOC_A_ID,
                "SOP-204 Rev.7",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 3, 1),
            ),
            _claim(
                DOC_B_ID,
                "MM-118",
                "primary",
                "filter replacement interval",
                "45 days",
                date(2022, 1, 1),
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c.status == "unresolved"
        assert c.equipment_id == EQUIPMENT_ID
        assert c.source_a_claim in ("30 days", "45 days")
        assert c.source_b_claim in ("30 days", "45 days")
        assert c.source_a_claim != c.source_b_claim

    def test_non_overlapping_validity_windows_no_conflict(self):
        """
        If one document's validity window has ended before the other begins,
        this is ordinary history, not a live conflict.
        Per docs/industrial/14_knowledge_conflict_detection.md step 4.
        """
        claims = [
            _claim(
                DOC_A_ID,
                "Old SOP",
                "primary",
                "filter replacement interval",
                "30 days",
                effective_from=date(2018, 1, 1),
                effective_until=date(2021, 12, 31),
            ),
            _claim(
                DOC_B_ID,
                "New SOP",
                "primary",
                "filter replacement interval",
                "45 days",
                effective_from=date(2022, 1, 1),
                effective_until=None,
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert conflicts == []

    def test_mixed_authority_still_surfaced(self):
        """
        Primary vs secondary: surfaced (not discarded) per step 3 — the
        secondary claim may mean a stale document needs updating.
        """
        claims = [
            _claim(
                DOC_A_ID,
                "SOP-204",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 1, 1),
            ),
            _claim(
                DOC_B_ID,
                "Vendor note",
                "secondary",
                "filter replacement interval",
                "45 days",
                date(2024, 1, 1),
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert len(conflicts) == 1
        assert conflicts[0].status == "unresolved"
        claims = [
            _claim(
                DOC_A_ID,
                "SOP-A",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 1, 1),
            ),
            _claim(
                DOC_B_ID,
                "SOP-B",
                "primary",
                "operating temperature",
                "120C",
                date(2024, 1, 1),
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert conflicts == []

    def test_synonym_normalization_triggers_conflict(self):
        """Parameters that normalize to the same canonical form should be compared."""
        claims = [
            _claim(DOC_A_ID, "SOP-A", "primary", "torque", "150 Nm", date(2024, 1, 1)),
            _claim(
                DOC_B_ID, "MM-B", "primary", "bolt torque", "120 Nm", date(2024, 1, 1)
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        # Both normalize to "tightening torque" and disagree → conflict
        assert len(conflicts) == 1

    def test_conflict_never_auto_resolved(self):
        """Confirm status is always 'unresolved' — resolution_note is None."""
        claims = [
            _claim(DOC_A_ID, "SOP", "primary", "interval", "30 days", date(2024, 1, 1)),
            _claim(
                DOC_B_ID, "Manual", "primary", "interval", "45 days", date(2024, 1, 1)
            ),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert all(c.status == "unresolved" for c in conflicts)
        assert all(c.resolution_note is None for c in conflicts)


# ---------------------------------------------------------------------------
# format_conflict_output
# ---------------------------------------------------------------------------


class TestSameRankNonPrimary:
    def test_secondary_pair_surfaces(self):
        claims = [
            _claim(DOC_A_ID, "Note A", "secondary", "interval", "30 days", date(2024, 1, 1)),
            _claim(DOC_B_ID, "Note B", "secondary", "interval", "45 days", date(2024, 1, 1)),
        ]
        conflicts = detect_conflicts(EQUIPMENT_ID, claims)
        assert len(conflicts) == 1
        assert conflicts[0].status == "unresolved"


class TestSameDocumentGuard:
    def test_same_document_claims_never_conflict(self):
        """Guard against double-counting one document as two sources."""
        claims = [
            _claim(
                DOC_A_ID,
                "SOP-204",
                "primary",
                "filter replacement interval",
                "30 days",
                date(2024, 1, 1),
            ),
            _claim(
                DOC_A_ID,
                "SOP-204",
                "primary",
                "filter replacement interval",
                "45 days",
                date(2024, 1, 1),
            ),
        ]
        assert detect_conflicts(EQUIPMENT_ID, claims) == []


class TestFormatConflictOutput:
    def test_output_matches_canonical_format(self):
        """The formatted output must match the exact format in the spec."""
        record = ConflictRecord(
            equipment_id=EQUIPMENT_ID,
            claim_description="Filter replacement interval for Equipment P-204",
            source_a_document_id=DOC_A_ID,
            source_a_document_name="SOP-204 Rev.7",
            source_a_authority="primary",
            source_a_effective_from=date(2024, 3, 1),
            source_a_claim="30 days",
            source_b_document_id=DOC_B_ID,
            source_b_document_name="Maintenance Manual MM-118",
            source_b_authority="primary",
            source_b_effective_from=date(2022, 1, 1),
            source_b_claim="45 days",
            status="unresolved",
        )
        output = format_conflict_output(record)
        assert output.startswith("CONFLICT DETECTED")
        assert "Filter replacement interval for Equipment P-204" in output
        assert "SOP-204 Rev.7" in output
        assert "Maintenance Manual MM-118" in output
        assert "30 days" in output
        assert "45 days" in output
        assert "Unresolved — requires human review" in output

    def test_closed_window_renders_range(self):
        """A superseded source shows its full window, not '–present'."""
        record = ConflictRecord(
            equipment_id=EQUIPMENT_ID,
            claim_description="Filter interval",
            source_a_document_id=DOC_A_ID,
            source_a_document_name="SOP-204 Rev.6",
            source_a_authority="primary",
            source_a_effective_from=date(2020, 1, 1),
            source_a_effective_until=date(2024, 2, 29),
            source_a_claim="30 days",
            source_b_document_id=DOC_B_ID,
            source_b_document_name="SOP-204 Rev.7",
            source_b_authority="primary",
            source_b_effective_from=date(2024, 3, 1),
            source_b_claim="30 days",
            status="unresolved",
        )
        output = format_conflict_output(record)
        assert "2020-01-01–2024-02-29" in output
        assert "2024-03-01–present" in output


class TestHttpInteropDates:
    """The /internal/detect-conflicts route accepts claims as raw JSON dicts,
    so effective_from/effective_until arrive as ISO STRINGS over HTTP. The
    detector must normalize them instead of crashing on str <= date."""

    def test_iso_date_strings_do_not_crash_and_still_detect(self):
        claims = [
            {"document_id": str(DOC_A_ID), "document_name": "SOP-204 Rev.6",
             "authority": "primary", "effective_from": "2020-01-01",
             "effective_until": None, "parameter": "Filter replacement interval",
             "value": "30 days"},
            {"document_id": str(DOC_B_ID), "document_name": "SOP-204 Rev.7",
             "authority": "primary", "effective_from": "2020-02-01T00:00:00Z",
             "effective_until": None, "parameter": "filter replacement interval",
             "value": "45 days"},
        ]
        records = detect_conflicts(EQUIPMENT_ID, claims)
        assert len(records) == 1
        assert records[0].status == "unresolved"

    def test_as_date_accepts_date_and_iso_string(self):
        from app.conflict_detection import _as_date
        assert _as_date(None) is None
        assert _as_date(date(2024, 1, 1)) == date(2024, 1, 1)
        assert _as_date("2024-01-01") == date(2024, 1, 1)
        assert _as_date("2024-01-01T00:00:00Z") == date(2024, 1, 1)
