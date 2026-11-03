import pytest

from calculation_engine.calculators import soil_carbon_calculator as sc

OBS = {
    "observation_id": "OBS-S1", "project_type": "soil_carbon", "project_id": "P1",
    "sample_id": "S1", "soc_percent": 1.0, "bulk_density": 1.3, "soil_depth": 30, "area": 2,
    "evidence_reference": "lab.pdf",
}


def test_normal_calculation(tmp_path):
    out = sc.run(OBS, tmp_path)
    result = out["record"]["result"]
    assert result["soc_stock_t_c_per_ha"] == 39.0           # 1.0 x 1.3 x 30
    assert result["carbon_stock_total_t_c"] == 78.0         # x 2 ha
    assert result["co2e_total_t"] == pytest.approx(78 * 44 / 12, abs=1e-3)


def test_gravel_fraction_reduces_the_stock(tmp_path):
    result = sc.run({**OBS, "gravel_fraction": 0.1}, tmp_path)["record"]["result"]
    assert result["soc_stock_t_c_per_ha"] == pytest.approx(35.1)


def test_default_gravel_is_recorded(tmp_path):
    record = sc.run(OBS, tmp_path)["record"]
    assert record["input_values"]["applied_defaults"] == {"gravel_fraction": 0}
    assert "DEFAULT_APPLIED" in [w["code"] for w in record["warnings"]]


def test_zero_soc_gives_zero_carbon(tmp_path):
    result = sc.run({**OBS, "soc_percent": 0}, tmp_path)["record"]["result"]
    assert result["co2e_total_t"] == 0


def test_boundary_soc_of_100_percent_is_accepted(tmp_path):
    assert sc.run({**OBS, "soc_percent": 100}, tmp_path)["status"] == "QA_PENDING"


def test_soc_above_100_is_rejected(tmp_path):
    assert sc.run({**OBS, "soc_percent": 100.1}, tmp_path)["status"] == "VALIDATION_FAILED"


def test_negative_and_zero_depth_are_rejected(tmp_path):
    assert sc.run({**OBS, "soil_depth": -5, "observation_id": "A"}, tmp_path)["status"] == "VALIDATION_FAILED"
    assert sc.run({**OBS, "soil_depth": 0, "observation_id": "B"}, tmp_path)["status"] == "VALIDATION_FAILED"


def test_depth_in_wrong_unit_is_rejected_not_silently_converted(tmp_path):
    out = sc.run({**OBS, "units": {"soil_depth": "m"}}, tmp_path)
    assert out["status"] == "VALIDATION_FAILED"
    assert out["validation"]["errors"][0]["code"] == "INVALID_UNIT"


def test_record_names_the_factor_used(tmp_path):
    factor = sc.run(OBS, tmp_path)["record"]["factors_used"][0]
    assert factor["factor_id"] == "FAC-001" and factor["version"] == "1.0"