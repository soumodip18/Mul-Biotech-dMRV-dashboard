"""Single entry point for the dMRV Calculation Engine.

Usage from code:
    from calculation_engine.engine import run_calculation
    outcome = run_calculation("METH-003", observation)

Usage from the command line (from the repository root):
    python -m calculation_engine.engine                       list methodologies
    python -m calculation_engine.engine METH-003 obs.json     run one observation file
"""

import json

from .calculators import soil_carbon_calculator, tree_carbon_calculator, tree_monitoring_calculator
from .records import RECORDS_DIR
from .validation.validator import METHODOLOGIES_DIR, load_methodology, validate_observation

# Which calculator handles which methodology
CALCULATORS = {
    "METH-001": tree_carbon_calculator,
    "METH-002": soil_carbon_calculator,
    "METH-003": tree_monitoring_calculator,
}


def available_methodologies():
    """List every methodology file and whether a calculator exists for it."""
    found = []
    for path in sorted(METHODOLOGIES_DIR.glob("*/METH-*.json")):
        with open(path, encoding="utf-8") as f:
            meth = json.load(f)
        found.append({
            "methodology_id": meth["methodology_id"],
            "name": meth["name"],
            "version": meth["version"],
            "status": meth.get("status"),
            "calculator_available": meth["methodology_id"] in CALCULATORS,
        })
    return found


def run_calculation(methodology_id, observation, records_dir=RECORDS_DIR):
    """Pick the right calculator, validate, calculate and save a record."""
    if load_methodology(methodology_id) is None:
        validation = validate_observation(observation, methodology_id)   # reports MISSING_METHODOLOGY
        return {"status": "VALIDATION_FAILED", "validation": validation.to_dict(), "record": None}

    calculator = CALCULATORS.get(methodology_id)
    if calculator is None:
        error = {"code": "NO_CALCULATOR", "field": "methodology_id",
                 "message": f"Methodology '{methodology_id}' exists but has no calculator yet."}
        return {"status": "NO_CALCULATOR",
                "validation": {"is_valid": False, "errors": [error], "warnings": []},
                "record": None}

    return calculator.run(observation, records_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        for m in available_methodologies():
            ready = "calculator ready" if m["calculator_available"] else "no calculator"
            print(f"{m['methodology_id']}  v{m['version']}  [{m['status']}]  {m['name']}  ({ready})")
    elif len(sys.argv) == 3:
        with open(sys.argv[2], encoding="utf-8") as f:
            observation = json.load(f)
        outcome = run_calculation(sys.argv[1], observation)
        print("Status:", outcome["status"])
        if outcome["record"]:
            print("Saved to:", outcome["file"])
            print(json.dumps(outcome["record"]["result"], indent=2))
        for e in outcome["validation"]["errors"]:
            print(f"  ERROR   {e['code']}: {e['message']}")
        for w in (outcome["record"] or {}).get("warnings", []):
            print(f"  WARNING {w['code']}: {w['message']}")
    else:
        print("Usage: python -m calculation_engine.engine [METHODOLOGY_ID observation.json]")