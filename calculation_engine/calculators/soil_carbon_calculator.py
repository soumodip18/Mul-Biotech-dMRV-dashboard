"""Calculator 2: Soil Organic Carbon (METH-002).

SOC stock (tC/ha) = SOC (%) x Bulk density (g/cm3) x Depth (cm) x (1 - Gravel fraction)
Total carbon (tC) = SOC stock x Area (ha)
CO2e (t)          = Total carbon x CO2 conversion factor (44/12, read from the factor file)
"""

import copy

from .. import ENGINE_VERSION
from ..factor_loader import factor_reference, load_factor
from ..records import RECORDS_DIR, create_and_save_record, used_observation_ids
from ..validation.validator import load_methodology, validate_observation

METHODOLOGY_ID = "METH-002"


def calculate_soc(soc_percent, bulk_density, soil_depth, area, gravel_fraction, co2e_factor):
    """The pure calculation. No validation and no saving happens here."""
    stock_per_ha = soc_percent * bulk_density * soil_depth * (1 - gravel_fraction)
    total_carbon = stock_per_ha * area
    return {
        "soc_stock_t_c_per_ha": round(stock_per_ha, 4),
        "carbon_stock_total_t_c": round(total_carbon, 4),
        "co2e_total_t": round(total_carbon * co2e_factor, 4),
    }


def run(observation, records_dir=RECORDS_DIR):
    """Validate, calculate and save a record. No record is created if validation fails."""
    methodology = load_methodology(METHODOLOGY_ID)
    known_ids = set()
    if methodology is not None:
        known_ids = used_observation_ids(METHODOLOGY_ID, methodology["version"],
                                         ENGINE_VERSION, records_dir)

    validation = validate_observation(observation, METHODOLOGY_ID, known_ids)
    if not validation.is_valid:
        return {"status": "VALIDATION_FAILED", "validation": validation.to_dict(), "record": None}

    # Load the CO2 factor named in the methodology
    factors_used = []
    co2e_factor = None
    for spec in methodology["factors_used"]:
        factor = load_factor(spec["file"])
        factors_used.append(factor_reference(spec["name"], spec["file"], factor))
        if spec["name"] == "carbon_to_co2e":
            co2e_factor = factor["value"]

    warnings = [vars(w) for w in validation.warnings]
    input_values = copy.deepcopy(observation)

    # Optional gravel fraction: record clearly when the default is applied
    gravel = observation.get("gravel_fraction")
    if gravel is None:
        gravel = 0
        input_values["applied_defaults"] = {"gravel_fraction": 0}
        warnings.append({"code": "DEFAULT_APPLIED", "field": "gravel_fraction",
                         "message": "gravel_fraction not supplied, 0 was used."})

    warnings.append({"code": "NO_STATED_UNCERTAINTY", "field": "uncertainty",
                     "message": "No laboratory uncertainty was supplied, so none is stated."})

    result = calculate_soc(observation["soc_percent"], observation["bulk_density"],
                           observation["soil_depth"], observation["area"], gravel, co2e_factor)

    record, path = create_and_save_record(
        project_id=observation["project_id"],
        methodology=methodology,
        input_observation_ids=[observation["observation_id"]],
        input_values=input_values,
        result=result,
        unit=methodology["output_units"],
        uncertainty={"value": None, "basis": methodology["uncertainty_rules"]},
        factors_used=factors_used,
        warnings=warnings,
        records_dir=records_dir,
    )
    return {"status": record["status"], "validation": validation.to_dict(),
            "record": record, "file": str(path)}


if __name__ == "__main__":
    import json

    sample = {
        "observation_id": "OBS-101", "project_type": "soil_carbon",
        "project_id": "MBF-DMRV-2026-001", "sample_id": "SAMPLE-A1",
        "soc_percent": 1.0, "bulk_density": 1.3, "soil_depth": 30, "area": 2,
        "evidence_reference": "lab_report_A1.pdf",
    }
    outcome = run(sample)
    print("Status:", outcome["status"])
    if outcome["record"]:
        print("Saved to:", outcome["file"])
        print(json.dumps(outcome["record"], indent=2))
    else:
        for e in outcome["validation"]["errors"]:
            print(f"  {e['code']}: {e['message']}")