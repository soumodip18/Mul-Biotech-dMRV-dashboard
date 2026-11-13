from calculation_engine import engine
from calculation_engine.records import load_records

MONITORING = {
    "observation_id": "OBS-E1", "project_type": "agroforestry", "project_id": "P1",
    "plot_id": "PLOT-A", "monitoring_date": "2026-10-22",
    "trees_planted": 100, "trees_surviving": 87, "evidence_reference": "photo.jpg",
}
SOIL = {
    "observation_id": "OBS-E2", "project_type": "soil_carbon", "project_id": "P1",
    "sample_id": "S1", "soc_percent": 1.0, "bulk_density": 1.3, "soil_depth": 30, "area": 2,
    "evidence_reference": "lab.pdf",
}
TREE = {
    "observation_id": "OBS-E3", "project_type": "agroforestry", "project_id": "P1", "plot_id": "X",
    "species": "EXAMPLE", "num_trees": 100, "survival_rate": 80, "dbh": 20, "height": 12,
    "wood_density": 0.6, "plot_area": 0.5, "biomass_equation": "EQ-001", "carbon_fraction": 0.47,
    "evidence_reference": "sheet.pdf",
}


def test_each_methodology_id_reaches_the_right_calculator(tmp_path):
    for meth_id, obs in (("METH-003", MONITORING), ("METH-002", SOIL), ("METH-001", TREE)):
        outcome = engine.run_calculation(meth_id, obs, tmp_path)
        assert outcome["status"] == "QA_PENDING"
        assert outcome["record"]["methodology_id"] == meth_id


def test_records_go_to_the_folder_that_was_given(tmp_path):
    engine.run_calculation("METH-003", MONITORING, tmp_path)
    assert [r["calculation_id"] for r in load_records(tmp_path)] == ["CALC-000001"]


def test_unknown_methodology_is_reported_and_creates_no_record(tmp_path):
    outcome = engine.run_calculation("METH-999", MONITORING, tmp_path)
    assert outcome["status"] == "VALIDATION_FAILED" and outcome["record"] is None
    assert outcome["validation"]["errors"][0]["code"] == "MISSING_METHODOLOGY"
    assert load_records(tmp_path) == []


def test_methodology_without_a_calculator_is_reported(tmp_path, monkeypatch):
    only_monitoring = {"METH-003": engine.CALCULATORS["METH-003"]}
    monkeypatch.setattr(engine, "CALCULATORS", only_monitoring)
    outcome = engine.run_calculation("METH-002", SOIL, tmp_path)
    assert outcome["status"] == "NO_CALCULATOR" and outcome["record"] is None
    assert outcome["validation"]["errors"][0]["code"] == "NO_CALCULATOR"


def test_invalid_input_is_passed_back_from_the_calculator(tmp_path):
    outcome = engine.run_calculation("METH-003", {**MONITORING, "trees_surviving": 500}, tmp_path)
    assert outcome["status"] == "VALIDATION_FAILED"
    assert outcome["validation"]["errors"][0]["code"] == "INVALID_RELATION"


def test_duplicate_is_blocked_through_the_entry_point(tmp_path):
    engine.run_calculation("METH-003", MONITORING, tmp_path)
    again = engine.run_calculation("METH-003", MONITORING, tmp_path)
    assert again["validation"]["errors"][0]["code"] == "DUPLICATE_OBSERVATION"


def test_available_methodologies_lists_all_three_with_calculators():
    found = {m["methodology_id"]: m for m in engine.available_methodologies()}
    assert set(found) == {"METH-001", "METH-002", "METH-003"}
    assert all(m["calculator_available"] for m in found.values())
    assert all("status" in m and "version" in m for m in found.values())