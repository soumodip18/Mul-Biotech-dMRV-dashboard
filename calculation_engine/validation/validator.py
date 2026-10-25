"""Input validation for the dMRV Calculation Engine.

An observation is a flat dictionary. Reserved keys:
    observation_id, project_type, evidence_reference, units
Every other key is treated as an input value for the methodology.
"""

import json
import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent.parent
METHODOLOGIES_DIR = ENGINE_ROOT / "methodologies"
RULES_FILE = Path(__file__).resolve().parent / "rules.json"

# Units the validator can compare exactly. Descriptive units such as
# "fraction 0 to 1" or "equation ID" are not checked.
CHECKABLE_UNITS = {"%", "g/cm3", "cm", "m", "ha", "count"}


@dataclass
class Issue:
    code: str
    field: str
    message: str


@dataclass
class ValidationResult:
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def is_valid(self):
        return len(self.errors) == 0

    def add_error(self, code, field_name, message):
        self.errors.append(Issue(code, field_name, message))

    def add_warning(self, code, field_name, message):
        self.warnings.append(Issue(code, field_name, message))

    def to_dict(self):
        return {
            "is_valid": self.is_valid,
            "errors": [vars(i) for i in self.errors],
            "warnings": [vars(i) for i in self.warnings],
        }


def load_methodology(methodology_id):
    """Find and load METH-xxx.json from any methodology folder. None if absent."""
    if not methodology_id:
        return None
    for path in METHODOLOGIES_DIR.glob(f"*/{methodology_id}.json"):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def load_rules():
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)["inputs"]


def _is_missing(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def _check_value(name, value, rule, result):
    """Check one value against its rule. Adds issues to result."""
    kind = rule.get("type")

    if kind == "string":
        if not isinstance(value, str):
            result.add_error("INVALID_TYPE", name, f"{name} must be text.")
        return

    if kind == "date":
        try:
            if isinstance(value, date):
                return
            date.fromisoformat(str(value))
        except ValueError:
            result.add_error("INVALID_TYPE", name, f"{name} must be a date in YYYY-MM-DD format.")
        return

    # numeric types
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        result.add_error("INVALID_TYPE", name, f"{name} must be a number.")
        return
    if isinstance(value, float) and not math.isfinite(value):
        result.add_error("INVALID_TYPE", name, f"{name} must be a finite number.")
        return
    if kind == "integer" and isinstance(value, float) and not value.is_integer():
        result.add_error("INVALID_TYPE", name, f"{name} must be a whole number.")
        return

    lo = rule.get("min")
    hi = rule.get("max")
    lo_inclusive = rule.get("min_inclusive", True)

    if lo is not None and lo >= 0 and value < 0:
        result.add_error("NEGATIVE_VALUE", name, f"{name} cannot be negative (got {value}).")
    elif lo is not None and (value < lo or (value == lo and not lo_inclusive)):
        word = "greater than" if not lo_inclusive else "at least"
        result.add_error("OUT_OF_RANGE", name, f"{name} must be {word} {lo} (got {value}).")
    elif hi is not None and value > hi:
        result.add_error("OUT_OF_RANGE", name, f"{name} must be at most {hi} (got {value}).")


def validate_observation(observation, methodology_id, known_observation_ids=None):
    """Validate one observation against one methodology.

    known_observation_ids: IDs already used, to detect duplicates.
    Returns a ValidationResult. Nothing is calculated here.
    """
    result = ValidationResult()

    methodology = load_methodology(methodology_id)
    if methodology is None:
        result.add_error("MISSING_METHODOLOGY", "methodology_id",
                         f"Methodology '{methodology_id}' was not found.")
        return result

    # Project type compatibility
    project_type = observation.get("project_type")
    if _is_missing(project_type):
        result.add_error("MISSING_INPUT", "project_type",
                         "project_type is required to check methodology compatibility.")
    elif project_type not in methodology.get("applicable_project_types", []):
        allowed = ", ".join(methodology.get("applicable_project_types", []))
        result.add_error("INCOMPATIBLE_PROJECT_TYPE", "project_type",
                         f"{methodology_id} does not apply to '{project_type}'. Allowed: {allowed}.")

    # Observation ID and duplicates
    obs_id = observation.get("observation_id")
    if _is_missing(obs_id):
        result.add_error("MISSING_INPUT", "observation_id", "observation_id is required.")
    elif known_observation_ids and obs_id in known_observation_ids:
        result.add_error("DUPLICATE_OBSERVATION", "observation_id",
                         f"Observation '{obs_id}' has already been used.")

    rules = load_rules()
    required = methodology.get("required_inputs", [])
    optional = methodology.get("optional_inputs", [])

    # Required inputs
    for spec in required:
        name = spec["name"]
        value = observation.get(name)
        if _is_missing(value):
            result.add_error("MISSING_INPUT", name, f"Required input '{name}' is missing.")
        elif name in rules:
            _check_value(name, value, rules[name], result)

    # Optional inputs, checked only when supplied
    for spec in optional:
        name = spec["name"]
        value = observation.get(name)
        if not _is_missing(value) and name in rules:
            _check_value(name, value, rules[name], result)

    # Units
    expected_units = {s["name"]: s.get("unit") for s in required + optional}
    for name, supplied in (observation.get("units") or {}).items():
        expected = expected_units.get(name)
        if expected in CHECKABLE_UNITS and str(supplied).strip().lower() != expected.lower():
            result.add_error("INVALID_UNIT", name,
                             f"{name} must be in '{expected}' but was given in '{supplied}'. "
                             "Automatic conversion is not applied in V1.")

    # Relationships between fields
    planted = observation.get("trees_planted")
    surviving = observation.get("trees_surviving")
    if (isinstance(planted, (int, float)) and isinstance(surviving, (int, float))
            and not isinstance(planted, bool) and not isinstance(surviving, bool)
            and surviving > planted):
        result.add_error("INVALID_RELATION", "trees_surviving",
                         f"trees_surviving ({surviving}) cannot be greater than trees_planted ({planted}).")

    # Evidence
    if _is_missing(observation.get("evidence_reference")):
        result.add_warning("MISSING_EVIDENCE", "evidence_reference",
                           "No evidence reference supplied. The result cannot be fully traced to evidence.")

    return result


if __name__ == "__main__":
    good = {
        "observation_id": "OBS-001", "project_type": "agroforestry",
        "project_id": "MBF-DMRV-2026-001", "plot_id": "PLOT-A",
        "monitoring_date": "2026-10-22", "trees_planted": 100, "trees_surviving": 87,
        "evidence_reference": "photo_plotA_2026-10-22.jpg",
    }
    cases = [
        ("Valid observation", good, "METH-003", None),
        ("Missing input", {k: v for k, v in good.items() if k != "trees_surviving"}, "METH-003", None),
        ("Negative value", {**good, "trees_surviving": -5}, "METH-003", None),
        ("Surviving more than planted", {**good, "trees_surviving": 150}, "METH-003", None),
        ("Zero planted", {**good, "trees_planted": 0}, "METH-003", None),
        ("Wrong project type", {**good, "project_type": "aquaculture"}, "METH-003", None),
        ("Unknown methodology", good, "METH-999", None),
        ("Duplicate observation", good, "METH-003", {"OBS-001"}),
        ("No evidence", {k: v for k, v in good.items() if k != "evidence_reference"}, "METH-003", None),
    ]
    for title, obs, meth, known in cases:
        res = validate_observation(obs, meth, known)
        print(f"\n{title}: {'PASS' if res.is_valid else 'FAIL'}")
        for i in res.errors:
            print(f"   ERROR   {i.code}: {i.message}")
        for i in res.warnings:
            print(f"   WARNING {i.code}: {i.message}")