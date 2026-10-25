"""Loads factor files so calculators never hard code constants."""

import json
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent


def load_factor(relative_path):
    """Load a factor file such as 'factors/emission_factors/co2_conversion.json'."""
    with open(ENGINE_ROOT / relative_path, encoding="utf-8") as f:
        return json.load(f)


def factor_reference(name, relative_path, factor):
    """A short description of a factor, stored in the calculation record."""
    return {
        "name": name,
        "file": relative_path,
        "factor_id": factor.get("factor_id"),
        "version": factor.get("version"),
        "value": factor.get("value"),
        "unit": factor.get("unit"),
    }