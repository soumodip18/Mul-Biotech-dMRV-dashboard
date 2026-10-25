import json

from calculation_engine import records
from calculation_engine.calculators import tree_monitoring_calculator as tm
from calculation_engine.records import load_records, used_observation_ids
from calculation_engine.validation.validator import load_methodology

OBS = {
    "observation_id": "OBS-A1", "project_type": "agroforestry", "project_id": "MBF-DMRV-2026-001",
    "plot_id": "PLOT-A", "monitoring_date": "2026-10-22",
    "trees_planted": 100, "trees_surviving": 87, "evidence_reference": "photo.jpg",
}

REQUIRED_FIELDS = {
    "calculation_id", "project_id", "methodology_id", "methodology_version",
    "input_observation_ids", "input_values", "formula", "result", "unit",
    "uncertainty", "status", "calculated_at", "engine_version",
}


def test_record_contains_every_required_field(tmp_path):
    record = tm.run(OBS, tmp_path)["record"]
    assert REQUIRED_FIELDS <= set(record)
    assert record["calculation_id"] == "CALC-000001"
    assert record["status"] == "QA_PENDING"
    assert record["engine_version"] == "v0.1.0"


def test_saved_file_matches_the_returned_record(tmp_path):
    out = tm.run(OBS, tmp_path)
    with open(out["file"], encoding="utf-8") as f:
        assert json.load(f) == out["record"]


def test_record_stores_the_exact_methodology_formula(tmp_path):
    record = tm.run(OBS, tmp_path)["record"]
    assert record["formula"] == load_methodology("METH-003")["formula"]


def test_record_keeps_a_copy_of_the_inputs_not_a_reference(tmp_path):
    obs = dict(OBS)
    record = tm.run(obs, tmp_path)["record"]
    obs["trees_surviving"] = 1                       # change the original afterwards
    assert record["input_values"]["trees_surviving"] == 87


def test_ids_increase_and_old_records_are_never_overwritten(tmp_path):
    first = tm.run(OBS, tmp_path)
    first_text = open(first["file"], encoding="utf-8").read()
    second = tm.run({**OBS, "observation_id": "OBS-A2"}, tmp_path)
    assert first["record"]["calculation_id"] == "CALC-000001"
    assert second["record"]["calculation_id"] == "CALC-000002"
    assert open(first["file"], encoding="utf-8").read() == first_text


def test_same_observation_cannot_be_calculated_twice_with_same_versions(tmp_path):
    tm.run(OBS, tmp_path)
    again = tm.run(OBS, tmp_path)
    assert again["status"] == "VALIDATION_FAILED"
    assert again["validation"]["errors"][0]["code"] == "DUPLICATE_OBSERVATION"
    assert len(load_records(tmp_path)) == 1


def test_methodology_version_change_allows_recalculation_and_keeps_both(tmp_path, monkeypatch):
    tm.run(OBS, tmp_path)
    newer = dict(load_methodology("METH-003"), version="1.1")
    monkeypatch.setattr(tm, "load_methodology", lambda _id: newer)
    second = tm.run(OBS, tmp_path)
    assert second["status"] == "QA_PENDING"
    saved = load_records(tmp_path)
    assert [r["methodology_version"] for r in saved] == ["1.0", "1.1"]
    assert [r["calculation_id"] for r in saved] == ["CALC-000001", "CALC-000002"]


def test_engine_version_change_allows_recalculation_and_keeps_both(tmp_path, monkeypatch):
    tm.run(OBS, tmp_path)
    # The engine version is read in two places, so change it in both
    monkeypatch.setattr(tm, "ENGINE_VERSION", "v0.2.0")
    monkeypatch.setattr(records, "ENGINE_VERSION", "v0.2.0")
    assert tm.run(OBS, tmp_path)["status"] == "QA_PENDING"
    saved = load_records(tmp_path)
    assert [r["engine_version"] for r in saved] == ["v0.1.0", "v0.2.0"]
    assert [r["calculation_id"] for r in saved] == ["CALC-000001", "CALC-000002"]