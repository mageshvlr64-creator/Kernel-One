from app.calculations import aggregate_values, check_tolerance, convert_unit
from app.inspection_logic import validate_drawing_caveat


def test_tolerance_pass_fail():
    assert check_tolerance(5.0, spec_min=1.0, spec_max=10.0).passed
    r = check_tolerance(12.0, spec_min=1.0, spec_max=10.0)
    assert not r.passed and r.deviation_percent == 20.0


def test_tolerance_nominal():
    assert check_tolerance(100.0, nominal=100.0, tolerance=5.0).passed
    assert not check_tolerance(110.0, nominal=100.0, tolerance=5.0).passed


def test_convert_unit():
    out = convert_unit(1000.0, "mm", "m")
    assert abs(out["converted_value"] - 1.0) < 1e-9


def test_convert_temperature_absolute():
    assert abs(convert_unit(32.0, "f", "c")["converted_value"] - 0.0) < 1e-9
    assert abs(convert_unit(100.0, "c", "f")["converted_value"] - 212.0) < 1e-9
    assert abs(convert_unit(20.0, "c", "c")["converted_value"] - 20.0) < 1e-9


def test_convert_unknown_fails():
    try:
        convert_unit(1.0, "furlong", "m")
        assert False
    except ValueError:
        pass


def test_aggregate():
    assert aggregate_values([1.0, 2.0, 3.0], "mean")["result"] == 2.0
    assert aggregate_values([1.0, 2.0, 3.0], "max")["result"] == 3.0


def test_drawing_caveat():
    assert validate_drawing_caveat(
        "Value read from drawing image, not independently verified."
    )
    assert not validate_drawing_caveat("The value is 42, certified correct.")
