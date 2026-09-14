"""
Unit tests for the document comparison / change detection engine.

Tests are written against docs/industrial/05_document_comparison.md and
docs/industrial/06_change_detection.md rules.

Run with: pytest services/industrial-service/tests/
"""

from __future__ import annotations

import uuid

import pytest

from app.comparison import (
    _normalize_parameter,
    compare_findings,
    is_low_confidence,
)
from app.models import DiffEntry


# ---------------------------------------------------------------------------
# Synonym normalisation
# ---------------------------------------------------------------------------


class TestNormalizeParameter:
    def test_exact_synonym_maps_to_canonical(self):
        assert _normalize_parameter("torque") == "tightening torque"
        assert _normalize_parameter("Tightening Force") == "tightening torque"
        assert _normalize_parameter("BOLT TORQUE") == "tightening torque"

    def test_unknown_parameter_returns_normalized_form(self):
        """Per spec: model never infers synonyms — only explicit table entries."""
        assert _normalize_parameter("seal wear") == "seal wear"
        assert _normalize_parameter("  Vibration Level  ") == "vibration level"


# ---------------------------------------------------------------------------
# compare_findings — basic cases
# ---------------------------------------------------------------------------


DOC_A = uuid.uuid4()
DOC_B = uuid.uuid4()


def _finding(
    parameter, value, location=None, confidence=1.0, evidence_id=None, source_kind=None
):
    finding = {
        "parameter": parameter,
        "value": value,
        "location_reference": location,
        "confidence": confidence,
        "evidence_id": str(evidence_id) if evidence_id else None,
    }
    if source_kind is not None:
        finding["source_kind"] = source_kind
    return finding


class TestCompareFindings:
    def test_identical_finding_produces_no_diff(self):
        fa = [_finding("torque", "150 Nm", "Flange A")]
        fb = [_finding("tightening torque", "150 Nm", "Flange A")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert diff.added == []
        assert diff.removed == []
        assert diff.changed == []

    def test_changed_value_detected(self):
        fa = [_finding("torque", "150 Nm", "Flange B")]
        fb = [_finding("torque", "130 Nm", "Flange B")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert len(diff.changed) == 1
        entry = diff.changed[0]
        assert entry.change_type == "changed"
        assert entry.value_in_document_a == "150 Nm"
        assert entry.value_in_document_b == "130 Nm"
        assert diff.added == []
        assert diff.removed == []

    def test_present_only_in_b_is_added(self):
        fa = []
        fb = [_finding("seal wear", "high")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert len(diff.added) == 1
        assert diff.added[0].change_type == "added"
        assert diff.removed == []

    def test_present_only_in_a_is_removed(self):
        fa = [_finding("seal wear", "high")]
        fb = []
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert len(diff.removed) == 1
        assert diff.removed[0].change_type == "removed"
        assert diff.added == []

    def test_ambiguous_near_match_reported_as_added_not_matched(self):
        """
        A finding in B that has no synonym mapping to A's parameter must be
        reported as 'added', per docs/industrial/06_change_detection.md:
        "a false match that hides a genuinely new finding is a worse failure
        mode than an extra 'added' entry."
        """
        fa = [_finding("corrosion rate", "0.1 mm/yr")]
        # Different parameter, no synonym mapping
        fb = [_finding("metal loss rate", "0.2 mm/yr")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        # "corrosion rate" has no match in B → removed
        # "metal loss rate" has no match in A → added
        assert len(diff.removed) == 1
        assert len(diff.added) == 1
        assert diff.changed == []

    def test_location_disambiguates_same_parameter(self):
        """Same parameter name, different locations → two independent findings."""
        fa = [
            _finding("torque", "150 Nm", "Flange A"),
            _finding("torque", "140 Nm", "Flange B"),
        ]
        fb = [
            _finding("torque", "150 Nm", "Flange A"),
            _finding("torque", "135 Nm", "Flange B"),  # different value at Flange B
        ]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        # Flange A is unchanged, Flange B is changed
        assert len(diff.changed) == 1
        assert diff.changed[0].location_reference == "Flange B"
        assert diff.added == []
        assert diff.removed == []

    def test_document_ids_propagated(self):
        fa = [_finding("torque", "100 Nm")]
        fb = [_finding("torque", "110 Nm")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert diff.document_a_id == DOC_A
        assert diff.document_b_id == DOC_B

    def test_confidence_is_min_of_both_sides(self):
        fa = [_finding("torque", "100 Nm", confidence=0.9)]
        fb = [_finding("torque", "110 Nm", confidence=0.6)]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert diff.changed[0].confidence == pytest.approx(0.6)


class TestIsLowConfidence:
    def test_below_threshold_is_low(self):
        entry = DiffEntry(
            change_type="changed",
            parameter="torque",
            confidence=0.5,
        )
        assert is_low_confidence(entry) is True

    def test_above_threshold_is_not_low(self):
        entry = DiffEntry(
            change_type="changed",
            parameter="torque",
            confidence=0.95,
        )
        assert is_low_confidence(entry) is False

    def test_none_confidence_is_not_flagged(self):
        entry = DiffEntry(
            change_type="added",
            parameter="torque",
            confidence=None,
        )
        assert is_low_confidence(entry) is False


class TestMatchingEdges:
    def test_location_mismatch_is_not_a_match(self):
        """Same parameter, different locations → added, never silently matched."""
        fa = [_finding("torque", "100 Nm", location="Flange A")]
        fb = [_finding("torque", "110 Nm", location="Flange B")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert diff.changed == []
        assert len(diff.added) == 1
        assert len(diff.removed) == 1

    def test_identical_values_produce_no_diff(self):
        fa = [_finding("torque", "100 Nm", location="Flange A")]
        fb = [_finding("torque", "100 Nm", location="Flange A")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert diff.added == [] and diff.removed == [] and diff.changed == []

    def test_synonym_parameters_match(self):
        fa = [_finding("torque", "100 Nm")]
        fb = [_finding("bolt torque", "110 Nm")]
        diff = compare_findings(DOC_A, DOC_B, fa, fb)
        assert len(diff.changed) == 1
        assert diff.changed[0].parameter == "tightening torque"

    def test_table_cap_applies_to_added_entries(self):
        diff = compare_findings(
            DOC_A, DOC_B, [], [_finding("torque", "110 Nm", source_kind="table")]
        )
        assert diff.added[0].confidence == 0.6
