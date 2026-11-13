import pytest

from calculation_engine.calculators import soil_carbon_calculator as sc
from calculation_engine.calculators import tree_carbon_calculator as tc
from calculation_engine.uncertainty.uncertainty import build_uncertainty
from calculation_engine.validation.validator import load_methodology

METH = {"uncertainty_rules": "rule text"}
RESULT = {"co2e_t": 100.0}


def codes(warnings):
    return [w["code"] for w in warnings]


def test_no_value_anywhere_is_flagged_not_invented():
    uncertainty, warnings = build_uncertainty(METH, RESULT)
    assert uncertainty == {"value": None, "basis": "rule text"}
    assert codes(warnings) == ["NO_STATED_UNCERTAINTY"]


def test_methodology_default_is_used_with_a_range():
    meth = {**METH, "default_uncertainty_percent": 20, "uncertainty_applies_to": "co2e_t"}
    uncertainty, warnings = build_uncertainty(meth, RESULT)
    assert uncertainty["value"] == 20 and uncertainty["source"] == "methodology default"
    assert uncertainty["applies_to"] == "co2e_t"
    assert uncertainty["lower"] == 80.0 and uncertainty["upper"] == 120.0
    assert warnings == []


def test_percent_without_applies_to_gives_no_range():
    uncertainty, _ = build_uncertainty({**METH, "default_uncertainty_percent": 20}, RESULT)
    assert uncertainty["value"] == 20 and "lower" not in uncertainty


def test_supplied_value_beats_the_default():
    meth = {**METH, "default_uncertainty_percent": 20}
    uncertainty, _ = build_uncertainty(meth, RESULT, supplied_percent=5)
    assert uncertainty["value"] == 5 and uncertainty["source"] == "supplied with the observation"


@pytest.mark.parametrize("bad", [-1, 100.5, "ten", True, float("nan")])
def test_invalid_supplied_value_is_ignored_with_a_warning(bad):
    uncertainty, warnings = build_uncertainty(METH, RESULT, supplied_percent=bad)
    assert uncertainty["value"] is None
    assert codes(warnings) == ["INVALID_UNCERTAINTY", "NO_STATED_UNCERTAINTY"]


def test_invalid_supplied_value_falls_back_to_a_valid_default():
    meth = {**METH, "default_uncertainty_percent": 15}
    uncertainty, warnings = build_uncertainty(meth, RESULT, supplied_percent=-3)
    assert uncertainty["value"] == 15
    assert codes(warnings) == ["INVALID_UNCERTAINTY"]


def test_invalid_default_is_ignored_with_a_warning():
    uncertainty, warnings = build_uncertainty({**METH, "default_uncertainty_percent": 250}, RESULT)
    assert uncertainty["value"] is None
    assert codes(warnings) == ["INVALID_UNCERTAINTY", "NO_STATED_UNCERTAINTY"]


def test_boundary_values_zero_and_one_hundred_percent():
    meth = {**METH, "uncertainty_applies_to": "co2e_t"}
    zero, _ = build_uncertainty(meth, RESULT, supplied_percent=0)
    assert zero["lower"] == zero["upper"] == 100.0
    full, _ = build_uncertainty(meth, RESULT, supplied_percent=100)
    assert full["lower"] == 0.0 and full["upper"] == 200.0


def test_non_numeric_result_field_gives_no_range():
    meth = {**METH, "default_uncertainty_percent": 10, "uncertainty_applies_to": "missing_field"}
    uncertainty, _ = build_uncertainty(meth, RESULT)
    assert uncertainty["value"] == 10 and "lower" not in uncertainty


SOIL = {
    "observation_id": "OBS-U1", "project_type": "soil_carbon", "project_id": "P1",
    "sample_id": "S1", "soc_percent": 1.0, "bulk_density": 1.3, "soil_depth": 30, "area": 2,
    "evidence_reference": "lab.pdf",
}


def test_soil_calculator_carries_a_laboratory_uncertainty(tmp_path, monkeypatch):
    meth = dict(load_methodology("METH-002"), uncertainty_applies_to="co2e_total_t")
    monkeypatch.setattr(sc, "load_methodology", lambda _id: meth)
    record = sc.run({**SOIL, "lab_uncertainty_percent": 10}, tmp_path)["record"]
    assert record["uncertainty"]["value"] == 10
    assert record["uncertainty"]["lower"] == pytest.approx(257.4, abs=1e-3)
    assert record["uncertainty"]["upper"] == pytest.approx(314.6, abs=1e-3)
    assert "NO_STATED_UNCERTAINTY" not in codes(record["warnings"])


def test_soil_calculator_still_works_with_an_invalid_laboratory_value(tmp_path):
    out = sc.run({**SOIL, "lab_uncertainty_percent": -4}, tmp_path)
    assert out["status"] == "QA_PENDING"
    assert out["record"]["uncertainty"]["value"] is None
    assert "INVALID_UNCERTAINTY" in codes(out["record"]["warnings"])


def test_tree_calculator_attaches_a_methodology_default(tmp_path, monkeypatch):
    meth = dict(load_methodology("METH-001"), default_uncertainty_percent=20,
                uncertainty_applies_to="co2e_t")
    monkeypatch.setattr(tc, "load_methodology", lambda _id: meth)
    obs = {
        "observation_id": "OBS-U2", "project_type": "agroforestry", "project_id": "P1", "plot_id": "X",
        "species": "EXAMPLE", "num_trees": 100, "survival_rate": 80, "dbh": 20, "height": 12,
        "wood_density": 0.6, "plot_area": 0.5, "biomass_equation": "EQ-001", "carbon_fraction": 0.47,
        "evidence_reference": "sheet.pdf",
    }
    record = tc.run(obs, tmp_path)["record"]
    co2e = record["result"]["co2e_t"]
    assert record["uncertainty"]["source"] == "methodology default"
    assert record["uncertainty"]["lower"] == pytest.approx(co2e * 0.8, abs=1e-3)
    assert record["uncertainty"]["upper"] == pytest.approx(co2e * 1.2, abs=1e-3)