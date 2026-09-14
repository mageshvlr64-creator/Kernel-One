"""
Engineering calculation helpers for the industrial domain.

Spec: docs/industrial/10_engineering_calculations.md,
      docs/industrial/11_calculation_verification.md

This module does NOT replace Character 2's Calculator Tool
(docs/features/07_calculator_tool/). It provides the deterministic,
domain-specific wrappers the industrial-service applies BEFORE calling
that tool (or when validating a tool result):

- tolerance / spec checking (measured vs {min,max} or {nominal,tolerance})
- explicit unit conversion step (never implicit mental conversion)
- aggregate statistics over retrieved finding values

Rule enforced here: every numeric claim this module produces carries the
inputs it was computed from, so the caller can attach an Evidence record
per input (input traceability) and a ToolInvocation citation. A numeric
claim stated without that citation is an unsupported claim.

What is NOT verified here (per 11_calculation_verification.md):
- whether the correct formula was chosen for the engineering context
- whether the extracted input values are themselves correct
Callers MUST frame answers with validate_calculation_framing().
"""

from __future__ import annotations

from dataclasses import dataclass, field


REQUIRED_CALC_FRAMING_HINT = (
    "arithmetic verified; formula selection and input values require human confirmation"
)


@dataclass
class ToleranceResult:
    measured_value: float
    spec_min: float | None = None
    spec_max: float | None = None
    passed: bool = False
    deviation_percent: float | None = None
    inputs: dict = field(default_factory=dict)


def check_tolerance(
    measured_value: float,
    spec_min: float | None = None,
    spec_max: float | None = None,
    nominal: float | None = None,
    tolerance: float | None = None,
) -> ToleranceResult:
    """Pass/fail plus percentage deviation, computed deterministically.

    Either (spec_min/spec_max) or (nominal/tolerance) must be given.
    nominal/tolerance expands to [nominal-tolerance, nominal+tolerance].
    deviation_percent is measured against the nearest bound (or nominal).
    """
    lo, hi = spec_min, spec_max
    if nominal is not None and tolerance is not None:
        lo, hi = nominal - tolerance, nominal + tolerance
    if lo is None and hi is None:
        raise ValueError("spec_min/spec_max or nominal/tolerance required")
    passed = (lo is None or measured_value >= lo) and (
        hi is None or measured_value <= hi
    )
    if passed:
        deviation: float | None = 0.0
    elif hi is not None and measured_value > hi and hi != 0:
        deviation = (measured_value - hi) / abs(hi) * 100.0
    elif lo is not None and measured_value < lo and lo != 0:
        deviation = (measured_value - lo) / abs(lo) * 100.0
    else:
        deviation = None
    return ToleranceResult(
        measured_value=measured_value,
        spec_min=lo,
        spec_max=hi,
        passed=passed,
        deviation_percent=deviation,
        inputs={
            "measured_value": measured_value,
            "spec_min": lo,
            "spec_max": hi,
        },
    )


UNIT_FACTORS_TO_SI: dict[str, float] = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "in": 0.0254,
    "ft": 0.3048,
    "psi": 6894.76,
    "kpa": 1000.0,
    "mpa": 1_000_000.0,
    "bar": 100_000.0,
    "c": 1.0,
    "f": 5.0 / 9.0,
}


def convert_unit(value: float, from_unit: str, to_unit: str) -> dict:
    """Explicit, auditable unit conversion step.

    Per 10_engineering_calculations.md: cross-unit comparisons go through
    this function rather than an implicit conversion. Raises ValueError
    on unknown units so callers fail closed instead of guessing.
    Temperature 'f' is handled as an interval scale (delta), not absolute.
    """
    fu, tu = from_unit.lower(), to_unit.lower()
    if fu not in UNIT_FACTORS_TO_SI or tu not in UNIT_FACTORS_TO_SI:
        raise ValueError(f"unsupported unit conversion: {from_unit} -> {to_unit}")
    si_value = value * UNIT_FACTORS_TO_SI[fu]
    converted = si_value / UNIT_FACTORS_TO_SI[tu]
    return {
        "input_value": value,
        "from_unit": from_unit,
        "to_unit": to_unit,
        "converted_value": converted,
    }


def aggregate_values(values: list[float], operation: str = "mean") -> dict:
    """Aggregate statistics computed over actual retrieved values.

    operation: one of mean|min|max|sum|count. Raises on empty input or
    unknown operation — never estimates.
    """
    if not values:
        raise ValueError("no values to aggregate")
    ops = {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "sum": sum(values),
        "count": float(len(values)),
    }
    if operation not in ops:
        raise ValueError(f"unsupported aggregation: {operation}")
    return {"operation": operation, "count": len(values), "result": ops[operation]}
