import json
from pathlib import Path

import pytest

from calculation_engine.engine import run_calculation

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

CASES = [
    ("METH-003", "meth-003_tree_monitoring"),
    ("METH-002", "meth-002_soil_carbon"),
    ("METH-001", "meth-001_tree_carbon"),
]


def load(name):
    with open(SAMPLES / name, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", CASES)
def test_sample_input_reproduces_the_expected_output(case, tmp_path):
    meth_id, stem = case
    expected = load(f"{stem}_expected_output.json")
    outcome = run_calculation(meth_id, load(f"{stem}_input.json"), tmp_path)

    assert outcome["status"] == expected["expected_status"] == "QA_PENDING"
    assert expected["methodology_id"] == meth_id
    result = outcome["record"]["result"]
    assert set(result) == set(expected["expected_result"])
    for name, value in expected["expected_result"].items():
        assert result[name] == pytest.approx(value, abs=1e-4)
    assert outcome["record"]["unit"] == expected["expected_units"]
    actual_codes = {w["code"] for w in outcome["record"]["warnings"]}
    assert set(expected["expected_warning_codes"]) <= actual_codes


@pytest.mark.parametrize("case", CASES)
def test_sample_files_are_clearly_labelled_as_not_real(case):
    _, stem = case
    sample_input = load(f"{stem}_input.json")
    assert sample_input["observation_id"].startswith("SAMPLE-")
    assert sample_input["project_id"].startswith("SAMPLE-")
    assert "SAMPLE" in sample_input["notes"]
    assert "SAMPLE DATA" in load(f"{stem}_expected_output.json")["sample_label"]


def test_expected_numbers_match_independent_hand_calculations():
    monitoring = load("meth-003_tree_monitoring_expected_output.json")["expected_result"]
    assert monitoring["survival_rate_percent"] == 87.0 and monitoring["mortality_count"] == 13

    soil = load("meth-002_soil_carbon_expected_output.json")["expected_result"]
    assert soil["soc_stock_t_c_per_ha"] == pytest.approx(1.0 * 1.3 * 30)
    assert soil["carbon_stock_total_t_c"] == pytest.approx(1.0 * 1.3 * 30 * 2)
    assert soil["co2e_total_t"] == pytest.approx(78 * 44 / 12, abs=1e-3)

    tree = load("meth-001_tree_carbon_expected_output.json")["expected_result"]
    agb_per_tree = 0.0673 * (0.6 * 20 ** 2 * 12) ** 0.976
    agb = agb_per_tree * 80 / 1000
    carbon = (agb + agb * 0.24) * 0.47
    assert tree["agb_per_tree_kg"] == pytest.approx(agb_per_tree, abs=1e-3)
    assert tree["above_ground_biomass_t"] == pytest.approx(agb, abs=1e-3)
    assert tree["carbon_stock_t_c"] == pytest.approx(carbon, abs=1e-3)
    assert tree["co2e_t"] == pytest.approx(carbon * 44 / 12, abs=1e-3)