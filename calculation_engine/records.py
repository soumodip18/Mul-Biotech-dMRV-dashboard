"""Calculation records: the permanent audit trail.

A record is never overwritten. Every calculation creates a new file
CALC-000001.json, CALC-000002.json, and so on.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from . import ENGINE_VERSION

RECORDS_DIR = Path(__file__).resolve().parent / "calculation_records"


def load_records(records_dir=RECORDS_DIR):
    """Return every saved record, oldest first."""
    records = []
    for path in sorted(Path(records_dir).glob("CALC-*.json")):
        with open(path, encoding="utf-8") as f:
            records.append(json.load(f))
    return records


def next_calculation_id(records_dir=RECORDS_DIR):
    numbers = []
    for path in Path(records_dir).glob("CALC-*.json"):
        try:
            numbers.append(int(path.stem.split("-")[1]))
        except (IndexError, ValueError):
            pass
    return f"CALC-{(max(numbers) if numbers else 0) + 1:06d}"


def used_observation_ids(methodology_id, methodology_version, engine_version=ENGINE_VERSION,
                         records_dir=RECORDS_DIR):
    """Observation IDs already calculated with this exact methodology and engine version.

    Recalculating under a NEW methodology or engine version is allowed, so it is
    not treated as a duplicate.
    """
    used = set()
    for record in load_records(records_dir):
        if (record.get("methodology_id") == methodology_id
                and record.get("methodology_version") == methodology_version
                and record.get("engine_version") == engine_version):
            used.update(record.get("input_observation_ids", []))
    return used


def create_and_save_record(*, project_id, methodology, input_observation_ids, input_values,
                           result, unit, uncertainty, factors_used=None, warnings=None,
                           status="QA_PENDING", records_dir=RECORDS_DIR):
    """Build a record and save it as a new file. Existing files are never touched."""
    records_dir = Path(records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)

    for _ in range(5):
        calculation_id = next_calculation_id(records_dir)
        record = {
            "calculation_id": calculation_id,
            "project_id": project_id,
            "methodology_id": methodology["methodology_id"],
            "methodology_version": methodology["version"],
            "input_observation_ids": list(input_observation_ids),
            "input_values": input_values,
            "formula": methodology["formula"],
            "factors_used": factors_used or [],
            "result": result,
            "unit": unit,
            "uncertainty": uncertainty,
            "warnings": warnings or [],
            "status": status,
            "calculated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "engine_version": ENGINE_VERSION,
        }
        path = records_dir / f"{calculation_id}.json"
        try:
            with open(path, "x", encoding="utf-8") as f:   # "x" refuses to overwrite
                json.dump(record, f, indent=2)
            return record, path
        except FileExistsError:
            continue
    raise RuntimeError("Could not create a unique calculation record.")