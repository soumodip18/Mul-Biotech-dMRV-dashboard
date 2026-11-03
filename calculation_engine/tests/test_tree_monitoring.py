import pytest

from calculation_engine.calculators import tree_monitoring_calculator as tm

OBS = {
    "observation_id": "OBS-M1", "project_type": "agroforestry", "project_id": "P1",
    "plot_id": "PLOT-A", "monitoring_date": "2026-10-22",
    "trees_planted": 100, "trees_surviving": 87, "evidence_reference": "photo.jpg",
}


def test_normal_calculation(tmp_path):
    out = tm.run(OBS, tmp_path)
    result = out["record"]["result"]
    assert out["status"] == "QA_PENDING"
    assert result["survival_rate_percent"] == 87.0
    assert result["mortality_count"] == 13
    assert result["mortality_percent"] == 13.0


def test_boundary_all_trees_survive(tmp_path):
    result = tm.run({**OBS, "trees_surviving": 100}, tmp_path)["record"]["result"]
    assert result["survival_rate_percent"] == 100.0 and result["mortality_count"] == 0


def test_zero_survivors(tmp_path):
    result = tm.run({**OBS, "trees_surviving": 0}, tmp_path)["record"]["result"]
    assert result["survival_rate_percent"] == 0.0 and result["mortality_percent"] == 100.0


def test_zero_planted_creates_no_record(tmp_path):
    out = tm.run({**OBS, "trees_planted": 0, "trees_surviving": 0}, tmp_path)
    assert out["status"] == "VALIDATION_FAILED" and out["record"] is None
    assert list(tmp_path.glob("CALC-*.json")) == []


def test_missing_input_creates_no_record(tmp_path):
    obs = {k: v for k, v in OBS.items() if k != "trees_surviving"}
    assert tm.run(obs, tmp_path)["status"] == "VALIDATION_FAILED"
    assert list(tmp_path.glob("CALC-*.json")) == []


def test_fractional_survival_is_calculated_without_rounding_errors(tmp_path):
    result = tm.run({**OBS, "trees_planted": 3, "trees_surviving": 1}, tmp_path)["record"]["result"]
    assert result["survival_rate_percent"] == pytest.approx(33.3333, abs=1e-4)