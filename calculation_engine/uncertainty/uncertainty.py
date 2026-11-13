"""Uncertainty handling.

V1 never invents an uncertainty value. A value is stated only when
  1. the observation supplies one (for example a laboratory result), or
  2. the methodology file defines default_uncertainty_percent.
Otherwise the result is flagged as having no stated uncertainty.

Optional methodology keys a reviewer can add:
    "default_uncertainty_percent": 20          (a number from 0 to 100)
    "uncertainty_applies_to": "co2e_t"         (the result field to put a range around)
"""

import math


def _valid_percent(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 100)


def build_uncertainty(methodology, result, supplied_percent=None):
    """Return (uncertainty, warnings).

    uncertainty is a dictionary stored in the calculation record.
    warnings is a list of warning dictionaries to add to the record.
    """
    basis = methodology.get("uncertainty_rules", "")
    warnings = []
    percent = None
    source = None

    if supplied_percent is not None:
        if _valid_percent(supplied_percent):
            percent, source = supplied_percent, "supplied with the observation"
        else:
            warnings.append({"code": "INVALID_UNCERTAINTY", "field": "lab_uncertainty_percent",
                             "message": "The supplied uncertainty must be a number from 0 to 100 and was ignored."})

    if percent is None:
        default = methodology.get("default_uncertainty_percent")
        if default is not None:
            if _valid_percent(default):
                percent, source = default, "methodology default"
            else:
                warnings.append({"code": "INVALID_UNCERTAINTY", "field": "default_uncertainty_percent",
                                 "message": "The methodology default uncertainty is not a number from 0 to 100 and was ignored."})

    if percent is None:
        warnings.append({"code": "NO_STATED_UNCERTAINTY", "field": "uncertainty",
                         "message": "No uncertainty is stated: none was supplied and the methodology has no default."})
        return {"value": None, "basis": basis}, warnings

    uncertainty = {"value": percent, "unit": "%", "source": source, "basis": basis}

    # Add a range around one result field when the methodology says which one
    key = methodology.get("uncertainty_applies_to")
    estimate = result.get(key) if key else None
    if isinstance(estimate, (int, float)) and not isinstance(estimate, bool):
        uncertainty["applies_to"] = key
        uncertainty["lower"] = round(estimate * (1 - percent / 100), 4)
        uncertainty["upper"] = round(estimate * (1 + percent / 100), 4)

    return uncertainty, warnings