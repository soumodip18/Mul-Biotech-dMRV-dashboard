"""Export calculation records to JSON and CSV for dashboards and reports.

Run from the repository root:
    python -m calculation_engine.export                 writes to calculation_engine/exports/
    python -m calculation_engine.export some_folder     writes to some_folder

Three files are written (they are derived data, so they are safe to regenerate):
    calculation_records.json    every full record, with an export notice
    calculation_records.csv     one row per calculation (summary)
    calculation_results.csv     one row per result value (long format, easy to chart)

Records themselves are only read, never changed.
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from . import ENGINE_VERSION
from .records import RECORDS_DIR, load_records

EXPORTS_DIR = Path(__file__).resolve().parent / "exports"
EXPORT_FORMAT_VERSION = "1.0"

NOTICE = ("All values are calculated or modelled results, not direct field observations. "
          "Records with status QA_PENDING have not been reviewed. Nothing in this export is a "
          "verified carbon credit or a claim of third party verification.")

RECORD_COLUMNS = [
    "calculation_id", "project_id", "methodology_id", "methodology_version", "engine_version",
    "status", "calculated_at", "input_observation_ids", "evidence_reference",
    "uncertainty_percent", "uncertainty_lower", "uncertainty_upper",
    "uncertainty_applies_to", "uncertainty_source",
    "factors_used", "warning_codes", "has_unapproved_factors",
]

RESULT_COLUMNS = [
    "calculation_id", "project_id", "methodology_id", "methodology_version", "status",
    "calculated_at", "result_name", "result_value", "result_unit",
]


def _safe_text(value):
    """Stop spreadsheet programs from running text that starts like a formula."""
    text = "" if value is None else str(value)
    if text and text[0] in "=+-@\t\r":
        return "'" + text
    return text


def _record_row(record):
    uncertainty = record.get("uncertainty") or {}
    warnings = record.get("warnings", [])
    factors = record.get("factors_used", [])
    inputs = record.get("input_values", {})
    return {
        "calculation_id": _safe_text(record["calculation_id"]),
        "project_id": _safe_text(record["project_id"]),
        "methodology_id": _safe_text(record["methodology_id"]),
        "methodology_version": _safe_text(record["methodology_version"]),
        "engine_version": _safe_text(record["engine_version"]),
        "status": _safe_text(record["status"]),
        "calculated_at": _safe_text(record["calculated_at"]),
        "input_observation_ids": _safe_text(";".join(record.get("input_observation_ids", []))),
        "evidence_reference": _safe_text(inputs.get("evidence_reference", "")),
        "uncertainty_percent": uncertainty.get("value"),
        "uncertainty_lower": uncertainty.get("lower"),
        "uncertainty_upper": uncertainty.get("upper"),
        "uncertainty_applies_to": _safe_text(uncertainty.get("applies_to", "")),
        "uncertainty_source": _safe_text(uncertainty.get("source", "")),
        "factors_used": _safe_text(";".join(f"{f.get('factor_id')}:v{f.get('version')}" for f in factors)),
        "warning_codes": _safe_text(";".join(w["code"] for w in warnings)),
        "has_unapproved_factors": "yes" if any(w["code"] == "UNAPPROVED_FACTOR" for w in warnings) else "no",
    }


def _result_rows(record):
    units = record.get("unit") or {}
    rows = []
    for name, value in record.get("result", {}).items():
        rows.append({
            "calculation_id": _safe_text(record["calculation_id"]),
            "project_id": _safe_text(record["project_id"]),
            "methodology_id": _safe_text(record["methodology_id"]),
            "methodology_version": _safe_text(record["methodology_version"]),
            "status": _safe_text(record["status"]),
            "calculated_at": _safe_text(record["calculated_at"]),
            "result_name": name,
            "result_value": value,
            "result_unit": _safe_text(units.get(name, "")),
        })
    return rows


def _write_csv(path, columns, rows):
    # utf-8-sig so that Excel opens special characters correctly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def export_records(records_dir=RECORDS_DIR, output_dir=EXPORTS_DIR):
    """Read every record in records_dir and write the three export files."""
    records = load_records(records_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "calculation_records.json"
    summary_path = output_dir / "calculation_records.csv"
    results_path = output_dir / "calculation_results.csv"

    package = {
        "export_format_version": EXPORT_FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine_version": ENGINE_VERSION,
        "notice": NOTICE,
        "record_count": len(records),
        "records": records,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(package, f, indent=2)

    _write_csv(summary_path, RECORD_COLUMNS, [_record_row(r) for r in records])
    _write_csv(results_path, RESULT_COLUMNS, [row for r in records for row in _result_rows(r)])

    return {"record_count": len(records),
            "files": [str(json_path), str(summary_path), str(results_path)]}


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else EXPORTS_DIR
    outcome = export_records(output_dir=target)
    print(f"Exported {outcome['record_count']} record(s):")
    for name in outcome["files"]:
        print("  ", name)