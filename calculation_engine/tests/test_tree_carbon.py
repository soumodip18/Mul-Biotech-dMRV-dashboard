import pytest

from calculation_engine.calculators import tree_carbon_calculator as tc
from calculation_engine.calculators.biomass_equations import chave_2014_pantropical

OBS = {
    "observation_id": "OBS-C1", "project_type": "agroforestry", "project_id": "P1", "plot_id": "X",
    "species": "EXAMPLE", "num_trees": 100, "survival_rate": 80, "dbh": 20, "height": 12,
    "wood_density": 0.6, "plot_area": 0.5, "biomass_equation": "EQ-001", "carbon_fraction": 0.47,
    "evidence_reference": "sheet.pdf",
}


def test_equation_matches_the_stated_formula():
    expected = 0.0673 * (0.6 * 20 ** 2 * 12) ** 0.976
    assert chave_2014_pantropical(0.6, 20, 12) == pytest.approx(expected)


def test_normal_calculation_matches_independent_hand_calculation(tmp_path):
    result = tc.run(OBS, tmp_path)["record"]["result"]
    agb_tree = 0.0673 * (0.6 * 400 * 12) ** 0.976
    agb = agb_tree * 80 / 1000
    carbon = (agb + agb * 0.24) * 0.47
    assert result["above_ground_biomass_t"] == pytest.approx(agb, abs=1e-3)
    assert result["carbon_stock_t_c"] == pytest.approx(carbon, abs=1e-3)
    assert result["co2e_t"] == pytest.approx(carbon * 44 / 12, abs=1e-3)
    assert result["carbon_stock_t_c_per_ha"] == pytest.approx(carbon / 0.5, abs=1e-3)


def test_supplied_root_shoot_ratio_overrides_default(tmp_path):
    record = tc.run({**OBS, "root_shoot_ratio": 0.2}, tmp_path)["record"]
    assert "applied_defaults" not in record["input_values"]
    assert record["result"]["below_ground_biomass_t"] == pytest.approx(
        record["result"]["above_ground_biomass_t"] * 0.2, abs=1e-3)


def test_unknown_equation_is_rejected(tmp_path):
    out = tc.run({**OBS, "biomass_equation": "EQ-999"}, tmp_path)
    assert out["status"] == "VALIDATION_FAILED"
    assert out["validation"]["errors"][0]["code"] == "UNKNOWN_EQUATION"


def test_zero_survival_gives_zero_carbon(tmp_path):
    result = tc.run({**OBS, "survival_rate": 0}, tmp_path)["record"]["result"]
    assert result["carbon_stock_t_c"] == 0 and result["co2e_t"] == 0


def test_out_of_range_wood_density_is_rejected(tmp_path):
    assert tc.run({**OBS, "wood_density": 5}, tmp_path)["status"] == "VALIDATION_FAILED"


def test_unapproved_factors_are_flagged_in_the_record(tmp_path):
    codes = [w["code"] for w in tc.run(OBS, tmp_path)["record"]["warnings"]]
    assert "UNAPPROVED_FACTOR" in codes


def test_unstated_uncertainty_is_flagged_not_invented(tmp_path):
    record = tc.run(OBS, tmp_path)["record"]
    assert record["uncertainty"]["value"] is None
    assert "NO_STATED_UNCERTAINTY" in [w["code"] for w in record["warnings"]]