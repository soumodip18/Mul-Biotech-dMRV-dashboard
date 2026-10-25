"""Calculator 1: Tree / Agroforestry Carbon (METH-001).

Surviving trees  = Number of trees x Survival rate / 100
AGB (t)          = AGB per tree (kg, from the selected equation) x Surviving trees / 1000
BGB (t)          = AGB x Root to shoot ratio
Total biomass    = AGB + BGB
Carbon (tC)      = Total biomass x Carbon fraction
CO2e (t)         = Carbon x CO2 conversion factor (44/12, read from the factor file)
"""

import copy

from .. import ENGINE_VERSION
from ..factor_loader import factor_reference, load_factor
from ..records import RECORDS_DIR, create_and_save_record, used_observation_ids
from ..validation.validator import load_methodology, validate_observation
from .biomass_equations import EQUATIONS

METHODOLOGY_ID = "METH-001"
UNAPPROVED = "DRAFT_PENDING_REVIEW"


def calculate_tree_carbon(num_trees, survival_rate, agb_per_tree_kg, root_shoot_ratio,
                          carbon_fraction, plot_area, co2e_factor):
    """The pure calculation. No validation and no saving happens here."""
    surviving = num_trees * survival_rate / 100
    agb = agb_per_tree_kg * surviving / 1000
    bgb = agb * root_shoot_ratio
    total = agb + bgb
    carbon = total * carbon_fraction
    return {
        "surviving_trees": round(surviving, 4),
        "agb_per_tree_kg": round(agb_per_tree_kg, 4),
        "above_ground_biomass_t": round(agb, 4),
        "below_ground_biomass_t": round(bgb, 4),
        "total_biomass_t": round(total, 4),
        "carbon_stock_t_c": round(carbon, 4),
        "co2e_t": round(carbon * co2e_factor, 4),
        "carbon_stock_t_c_per_ha": round(carbon / plot_area, 4),
    }


def run(observation, records_dir=RECORDS_DIR):
    """Validate, calculate and save a record. No record is created if validation fails."""
    methodology = load_methodology(METHODOLOGY_ID)
    known_ids = set()
    if methodology is not None:
        known_ids = used_observation_ids(METHODOLOGY_ID, methodology["version"],
                                         ENGINE_VERSION, records_dir)

    validation = validate_observation(observation, METHODOLOGY_ID, known_ids)

    # The selected equation must exist in the factor file AND in the code registry
    spec_by_name = {s["name"]: s for s in methodology["factors_used"]} if methodology else {}
    equation_entry = None
    if validation.is_valid:
        eq_id = observation["biomass_equation"]
        eq_file = load_factor(spec_by_name["allometric_equations"]["file"])
        equation_entry = next((e for e in eq_file["equations"] if e["equation_id"] == eq_id), None)
        if equation_entry is None or eq_id not in EQUATIONS:
            validation.add_error("UNKNOWN_EQUATION", "biomass_equation",
                                 f"Equation '{eq_id}' is not available in the engine.")

    if not validation.is_valid:
        return {"status": "VALIDATION_FAILED", "validation": validation.to_dict(), "record": None}

    warnings = [vars(w) for w in validation.warnings]
    factors_used = []
    input_values = copy.deepcopy(observation)

    # Equation
    eq_ref = factor_reference("allometric_equations", spec_by_name["allometric_equations"]["file"], eq_file)
    eq_ref["applied"] = equation_entry
    factors_used.append(eq_ref)
    if equation_entry.get("status") == UNAPPROVED:
        warnings.append({"code": "UNAPPROVED_FACTOR", "field": "biomass_equation",
                         "message": f"Equation {equation_entry['equation_id']} is pending review."})
    agb_per_tree = EQUATIONS[observation["biomass_equation"]](
        observation["wood_density"], observation["dbh"], observation["height"])

    # Root to shoot ratio: use the supplied value, otherwise the factor file default
    root_shoot = observation.get("root_shoot_ratio")
    if root_shoot is None:
        rs_spec = spec_by_name["root_shoot_ratios"]
        rs_file = load_factor(rs_spec["file"])
        entry = next(v for v in rs_file["values"] if v["applies_to"] == "default_tropical_tree")
        root_shoot = entry["value"]
        rs_ref = factor_reference("root_shoot_ratios", rs_spec["file"], rs_file)
        rs_ref["applied"] = entry
        factors_used.append(rs_ref)
        input_values["applied_defaults"] = {"root_shoot_ratio": root_shoot}
        warnings.append({"code": "DEFAULT_APPLIED", "field": "root_shoot_ratio",
                         "message": f"root_shoot_ratio not supplied, default {root_shoot} was used."})
        if entry.get("status") == UNAPPROVED:
            warnings.append({"code": "UNAPPROVED_FACTOR", "field": "root_shoot_ratio",
                             "message": "The default root to shoot ratio is pending review."})

    # CO2 conversion
    co2_spec = spec_by_name["carbon_to_co2e"]
    co2_file = load_factor(co2_spec["file"])
    factors_used.append(factor_reference("carbon_to_co2e", co2_spec["file"], co2_file))

    result = calculate_tree_carbon(
        observation["num_trees"], observation["survival_rate"], agb_per_tree, root_shoot,
        observation["carbon_fraction"], observation["plot_area"], co2_file["value"])

    # Uncertainty: only stated if the methodology file provides a value
    pct = methodology.get("default_uncertainty_percent")
    if pct is None:
        uncertainty = {"value": None, "basis": methodology["uncertainty_rules"]}
        warnings.append({"code": "NO_STATED_UNCERTAINTY", "field": "uncertainty",
                         "message": "The methodology gives no default uncertainty value yet."})
    else:
        uncertainty = {"value": pct, "unit": "%", "basis": methodology["uncertainty_rules"]}

    record, path = create_and_save_record(
        project_id=observation["project_id"],
        methodology=methodology,
        input_observation_ids=[observation["observation_id"]],
        input_values=input_values,
        result=result,
        unit=methodology["output_units"],
        uncertainty=uncertainty,
        factors_used=factors_used,
        warnings=warnings,
        records_dir=records_dir,
    )
    return {"status": record["status"], "validation": validation.to_dict(),
            "record": record, "file": str(path)}


if __name__ == "__main__":
    import json

    sample = {
        "observation_id": "OBS-201", "project_type": "agroforestry",
        "project_id": "MBF-DMRV-2026-001", "plot_id": "PLOT-A",
        "species": "EXAMPLE_SPECIES", "num_trees": 100, "survival_rate": 80,
        "dbh": 20, "height": 12, "wood_density": 0.6, "plot_area": 0.5,
        "biomass_equation": "EQ-001", "carbon_fraction": 0.47,
        "evidence_reference": "field_sheet_plotA.pdf",
    }
    outcome = run(sample)
    print("Status:", outcome["status"])
    if outcome["record"]:
        print("Saved to:", outcome["file"])
        print(json.dumps(outcome["record"]["result"], indent=2))
        for w in outcome["record"]["warnings"]:
            print(f"  WARNING {w['code']}: {w['message']}")
    else:
        for e in outcome["validation"]["errors"]:
            print(f"  {e['code']}: {e['message']}")