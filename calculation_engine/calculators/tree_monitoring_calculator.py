"""Calculator 3: Tree Monitoring (METH-003).

Survival Rate (%) = Surviving Trees / Planted Trees x 100
"""

import copy

from .. import ENGINE_VERSION
from ..records import RECORDS_DIR, create_and_save_record, used_observation_ids
from ..validation.validator import load_methodology, validate_observation

METHODOLOGY_ID = "METH-003"


def calculate_survival(trees_planted, trees_surviving):
    """The pure calculation. No validation and no saving happens here."""
    survival_rate = trees_surviving / trees_planted * 100
    return {
        "trees_planted": trees_planted,
        "trees_surviving": trees_surviving,
        "mortality_count": trees_planted - trees_surviving,
        "survival_rate_percent": round(survival_rate, 4),
        "mortality_percent": round(100 - survival_rate, 4),
    }


def run(observation, records_dir=RECORDS_DIR):
    """Validate, calculate and save a record.

    Returns a dictionary with status, validation details and the saved record.
    If validation fails nothing is calculated and no record is created.
    """
    methodology = load_methodology(METHODOLOGY_ID)
    known_ids = set()
    if methodology is not None:
        known_ids = used_observation_ids(METHODOLOGY_ID, methodology["version"],
                                         ENGINE_VERSION, records_dir)

    validation = validate_observation(observation, METHODOLOGY_ID, known_ids)
    if not validation.is_valid:
        return {"status": "VALIDATION_FAILED", "validation": validation.to_dict(), "record": None}

    result = calculate_survival(observation["trees_planted"], observation["trees_surviving"])

    record, path = create_and_save_record(
        project_id=observation["project_id"],
        methodology=methodology,
        input_observation_ids=[observation["observation_id"]],
        input_values=copy.deepcopy(observation),
        result=result,
        unit=methodology["output_units"],
        uncertainty={"value": None, "basis": methodology["uncertainty_rules"]},
        warnings=[vars(w) for w in validation.warnings],
        records_dir=records_dir,
    )
    return {"status": record["status"], "validation": validation.to_dict(),
            "record": record, "file": str(path)}


if __name__ == "__main__":
    import json

    sample = {
        "observation_id": "OBS-001", "project_type": "agroforestry",
        "project_id": "MBF-DMRV-2026-001", "plot_id": "PLOT-A",
        "monitoring_date": "2026-10-22", "trees_planted": 100, "trees_surviving": 87,
        "evidence_reference": "photo_plotA_2026-10-22.jpg",
    }
    outcome = run(sample)
    print("Status:", outcome["status"])
    if outcome["record"]:
        print("Saved to:", outcome["file"])
        print(json.dumps(outcome["record"], indent=2))
    else:
        for e in outcome["validation"]["errors"]:
            print(f"  {e['code']}: {e['message']}")