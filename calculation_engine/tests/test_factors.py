import pytest

from calculation_engine.factor_loader import load_factor


def test_co2_factor_is_the_molecular_weight_ratio():
    assert load_factor("factors/emission_factors/co2_conversion.json")["value"] == pytest.approx(44 / 12, abs=1e-6)


def test_unit_conversions_are_consistent_in_both_directions():
    conversions = load_factor("factors/conversion_factors/units.json")["conversions"]
    lookup = {(c["from"], c["to"]): c["multiply_by"] for c in conversions}
    for (a, b), factor in lookup.items():
        if (b, a) in lookup:
            assert factor * lookup[(b, a)] == pytest.approx(1.0)


def test_every_factor_file_in_the_methodologies_exists():
    from calculation_engine.validation.validator import load_methodology
    for meth_id in ("METH-001", "METH-002", "METH-003"):
        for spec in load_methodology(meth_id)["factors_used"]:
            assert load_factor(spec["file"]) is not None