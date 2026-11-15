import csv
import json

from calculation_engine import engine
from calculation_engine.calculators import soil_carbon_calculator as sc
from calculation_engine.export import NOTICE, RECORD_COLUMNS, RESULT_COLUMNS, export_records
from calculation_engine.records import load_records
from calculation_engine.validation.validator import load_methodology

MONITORING = {
    "observation_id": "OBS-X1", "project_type": "agroforestry", "project_id": "P1",
    "plot_id": "PLOT-A", "monitoring_date": "2026-10-22",
    "trees_planted": 100, "trees_surviving": 87, "evidence_reference": "photo.jpg",
}
SOIL = {
    "observation_id": "OBS-X2", "project_type": "soil_carbon", "project_id": "P1",
    "sample_id": "S1", "soc_percent": 1.0, "bulk_density": 1.3, "soil_depth": 30, "area": 2,
    "evidence_reference": "lab.pdf",
}
TREE = {
    "observation_id": "OBS-X3", "project_type": "agroforestry", "project_id": "P1", "plot_id": "X",
    "species": "EXAMPLE", "num_trees": 100, "survival_rate": 80, "dbh": 20, "height": 12,
    "wood_density": 0.6, "plot_area": 0.5, "biomass_equation": "EQ-001", "carbon_fraction": 0.47,
    "evidence_reference": "sheet.pdf",
}


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def make_records(folder):
    engine.run_calculation("METH-003", MONITORING, folder)
    engine.run_calculation("METH-002", SOIL, folder)
    engine.run_calculation("METH-001", TREE, folder)


def test_empty_records_folder_gives_empty_files_with_headers(tmp_path):
    outcome = export_records(tmp_path / "records", tmp_path / "out")
    assert outcome["record_count"] == 0
    json_file, summary, results = [tmp_path / "out" / n for n in
                                   ("calculation_records.json", "calculation_records.csv", "calculation_results.csv")]
    assert json.load(open(json_file, encoding="utf-8"))["record_count"] == 0
    assert read_csv(summary) == [] and read_csv(results) == []
    assert open(summary, encoding="utf-8-sig").readline().strip().split(",") == RECORD_COLUMNS


def test_json_export_contains_every_record_and_the_notice(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    package = json.load(open(tmp_path / "out" / "calculation_records.json", encoding="utf-8"))
    assert package["record_count"] == 3
    assert package["notice"] == NOTICE and "verified carbon credit" in package["notice"]
    assert package["records"] == load_records(tmp_path / "records")
    assert package["engine_version"] == "v0.1.0"


def test_summary_csv_has_one_row_per_calculation(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    rows = read_csv(tmp_path / "out" / "calculation_records.csv")
    assert [r["calculation_id"] for r in rows] == ["CALC-000001", "CALC-000002", "CALC-000003"]
    assert [r["methodology_id"] for r in rows] == ["METH-003", "METH-002", "METH-001"]
    assert all(r["status"] == "QA_PENDING" for r in rows)
    assert rows[0]["input_observation_ids"] == "OBS-X1"
    assert rows[0]["evidence_reference"] == "photo.jpg"


def test_summary_csv_shows_factors_warnings_and_unapproved_flag(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    monitoring, soil, tree = read_csv(tmp_path / "out" / "calculation_records.csv")
    assert monitoring["factors_used"] == "" and monitoring["warning_codes"] == ""
    assert monitoring["has_unapproved_factors"] == "no"
    assert soil["factors_used"] == "FAC-001:v1.0"
    assert "NO_STATED_UNCERTAINTY" in soil["warning_codes"].split(";")
    assert tree["has_unapproved_factors"] == "yes"
    assert "UNAPPROVED_FACTOR" in tree["warning_codes"].split(";")


def test_unstated_uncertainty_is_left_blank_not_zero(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    for row in read_csv(tmp_path / "out" / "calculation_records.csv"):
        assert row["uncertainty_percent"] == "" and row["uncertainty_lower"] == ""


def test_stated_uncertainty_is_exported_with_its_range(tmp_path, monkeypatch):
    meth = dict(load_methodology("METH-002"), uncertainty_applies_to="co2e_total_t")
    monkeypatch.setattr(sc, "load_methodology", lambda _id: meth)
    sc.run({**SOIL, "lab_uncertainty_percent": 10}, tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    row = read_csv(tmp_path / "out" / "calculation_records.csv")[0]
    assert float(row["uncertainty_percent"]) == 10
    assert float(row["uncertainty_lower"]) == 257.4 and float(row["uncertainty_upper"]) == 314.6
    assert row["uncertainty_applies_to"] == "co2e_total_t"
    assert row["uncertainty_source"] == "supplied with the observation"


def test_results_csv_has_one_row_per_result_value_with_units(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    rows = read_csv(tmp_path / "out" / "calculation_results.csv")
    assert list(rows[0].keys()) == RESULT_COLUMNS
    assert len(rows) == 5 + 3 + 8                      # monitoring + soil + tree result fields
    co2e = [r for r in rows if r["result_name"] == "co2e_total_t"][0]
    assert co2e["calculation_id"] == "CALC-000002" and co2e["result_unit"] == "tCO2e"
    assert float(co2e["result_value"]) == 286.0
    survival = [r for r in rows if r["result_name"] == "survival_rate_percent"][0]
    assert survival["result_unit"] == "%" and float(survival["result_value"]) == 87.0


def test_text_that_looks_like_a_formula_is_neutralised(tmp_path):
    engine.run_calculation("METH-003", {**MONITORING, "evidence_reference": "=1+1"}, tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    row = read_csv(tmp_path / "out" / "calculation_records.csv")[0]
    assert row["evidence_reference"] == "'=1+1"


def test_export_never_changes_or_adds_records(tmp_path):
    make_records(tmp_path / "records")
    before = {p.name: p.read_text(encoding="utf-8") for p in (tmp_path / "records").glob("*")}
    export_records(tmp_path / "records", tmp_path / "out")
    after = {p.name: p.read_text(encoding="utf-8") for p in (tmp_path / "records").glob("*")}
    assert before == after and len(after) == 3


def test_exporting_again_replaces_the_old_export_cleanly(tmp_path):
    make_records(tmp_path / "records")
    export_records(tmp_path / "records", tmp_path / "out")
    outcome = export_records(tmp_path / "records", tmp_path / "out")
    assert outcome["record_count"] == 3
    assert len(read_csv(tmp_path / "out" / "calculation_records.csv")) == 3