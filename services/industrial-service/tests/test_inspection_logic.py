"""
Unit tests for inspection domain logic.

Tests the domain rules from docs/industrial/02_inspection_reports.md,
04_sop_compliance.md, and 11_calculation_verification.md.
"""

from __future__ import annotations

from app.inspection_logic import (
    Finding,
    is_supported_finding,
    needs_ocr_confidence_warning,
    validate_answer_disclaimers,
    validate_calculation_framing,
    validate_sop_compliance_disclaimer,
    format_finding_answer_fragment,
    OCR_CONFIDENCE_WARN_THRESHOLD,
)


class TestSupportedFinding:
    def test_all_evidence_ids_present_is_supported(self):
        finding = Finding(
            parameter="Bolt torque",
            measured_value="15% below spec",
            specification="150 Nm",
            pass_fail="FAIL",
            location_reference="Flange B, page 4",
            evidence_id_parameter="ev-001",
            evidence_id_measured_value="ev-002",
            evidence_id_specification="ev-003",
            evidence_id_pass_fail="ev-004",
        )
        assert is_supported_finding(finding) is True

    def test_missing_one_evidence_id_is_unsupported(self):
        """A finding that cites only the pass/fail without measured value/threshold
        is an unsupported claim per docs/industrial/02_inspection_reports.md."""
        finding = Finding(
            parameter="Bolt torque",
            measured_value=None,
            specification=None,
            pass_fail="FAIL",
            location_reference="Flange B",
            evidence_id_parameter="ev-001",
            evidence_id_measured_value=None,  # missing
            evidence_id_specification=None,  # missing
            evidence_id_pass_fail="ev-004",
        )
        assert is_supported_finding(finding) is False


class TestOcrConfidenceWarning:
    def test_below_threshold_needs_warning(self):
        finding = Finding(
            parameter="torque",
            measured_value="150 Nm",
            specification="165 Nm",
            pass_fail="FAIL",
            location_reference=None,
            ocr_confidence=0.70,
        )
        assert needs_ocr_confidence_warning(finding) is True

    def test_at_threshold_no_warning(self):
        finding = Finding(
            parameter="torque",
            measured_value="150 Nm",
            specification="165 Nm",
            pass_fail="FAIL",
            location_reference=None,
            ocr_confidence=OCR_CONFIDENCE_WARN_THRESHOLD,
        )
        assert needs_ocr_confidence_warning(finding) is False

    def test_above_threshold_no_warning(self):
        finding = Finding(
            parameter="torque",
            measured_value="150 Nm",
            specification="165 Nm",
            pass_fail="FAIL",
            location_reference=None,
            ocr_confidence=0.95,
        )
        assert needs_ocr_confidence_warning(finding) is False

    def test_none_confidence_no_warning(self):
        finding = Finding(
            parameter="torque",
            measured_value="150 Nm",
            specification=None,
            pass_fail=None,
            location_reference=None,
            ocr_confidence=None,
        )
        assert needs_ocr_confidence_warning(finding) is False


class TestFormatFindingAnswerFragment:
    def test_low_confidence_includes_warning_text(self):
        finding = Finding(
            parameter="Bolt torque",
            measured_value="130 Nm",
            specification="150 Nm",
            pass_fail="15% below spec",
            location_reference="Flange B",
            ocr_confidence=0.60,
        )
        fragment = format_finding_answer_fragment(finding)
        assert "OCR confidence lower than usual" in fragment
        assert "verify against the original document" in fragment

    def test_high_confidence_no_warning(self):
        finding = Finding(
            parameter="Bolt torque",
            measured_value="130 Nm",
            specification="150 Nm",
            pass_fail="15% below spec",
            location_reference="Flange B",
            ocr_confidence=0.99,
        )
        fragment = format_finding_answer_fragment(finding)
        assert "OCR confidence" not in fragment


class TestSopComplianceDisclaimer:
    def test_compliant_answer_passes(self):
        answer = (
            "The maintenance record's described action matches Step 3 of SOP-1147, "
            "based on the text of the SOP document provided, "
            "not an independent regulatory assessment."
        )
        assert validate_sop_compliance_disclaimer(answer) is True

    def test_answer_without_disclaimer_fails(self):
        answer = "The maintenance record's action matches the SOP."
        assert validate_sop_compliance_disclaimer(answer) is False


class TestCalculationFramingValidation:
    def test_compliant_calculation_answer_passes(self):
        answer = (
            "The deviation is 12.5% (arithmetic verified). "
            "Formula selection and input values require human confirmation."
        )
        assert validate_calculation_framing(answer) is True

    def test_answer_without_framing_fails(self):
        answer = "The deviation is 12.5%."
        assert validate_calculation_framing(answer) is False


class TestValidateAnswerDisclaimers:
    def test_sop_kind_requires_disclaimer(self):
        out = validate_answer_disclaimers("Matches Step 3.", "sop")
        assert out == {"valid": False, "missing": ["sop_disclaimer"]}

    def test_general_kind_has_no_requirements(self):
        assert validate_answer_disclaimers("Anything.", "general") == {
            "valid": True,
            "missing": [],
        }

    def test_unknown_kind_fails_closed(self):
        try:
            validate_answer_disclaimers("Anything.", "audit")
            assert False, "should have raised"
        except ValueError:
            pass
