from calculation_engine.validation.validator import validate_observation

GOOD = {
    "observation_id": "OBS-T1", "project_type": "agroforestry",
    "project_id": "P1", "plot_id": "PLOT-A", "monitoring_date": "2026-10-22",
    "trees_planted": 100, "trees_surviving": 87, "evidence_reference": "photo.jpg",
}


def codes(result):
    return [e.code for e in result.errors]


def test_valid_observation_passes():
    result = validate_observation(GOOD, "METH-003")
    assert result.is_valid and not result.errors and not result.warnings


def test_missing_input_is_flagged():
    obs = {k: v for k, v in GOOD.items() if k != "trees_surviving"}
    assert "MISSING_INPUT" in codes(validate_observation(obs, "METH-003"))


def test_empty_string_counts_as_missing():
    assert "MISSING_INPUT" in codes(validate_observation({**GOOD, "plot_id": "  "}, "METH-003"))


def test_negative_value_is_flagged():
    assert "NEGATIVE_VALUE" in codes(validate_observation({**GOOD, "trees_surviving": -1}, "METH-003"))


def test_invalid_type_is_flagged():
    assert "INVALID_TYPE" in codes(validate_observation({**GOOD, "trees_planted": "many"}, "METH-003"))
    assert "INVALID_TYPE" in codes(validate_observation({**GOOD, "trees_planted": 10.5}, "METH-003"))
    assert "INVALID_TYPE" in codes(validate_observation({**GOOD, "monitoring_date": "22/10/2026"}, "METH-003"))


def test_boolean_is_not_accepted_as_a_number():
    assert "INVALID_TYPE" in codes(validate_observation({**GOOD, "trees_planted": True}, "METH-003"))


def test_zero_planted_is_rejected():
    assert "OUT_OF_RANGE" in codes(validate_observation({**GOOD, "trees_planted": 0}, "METH-003"))


def test_zero_surviving_is_allowed():
    assert validate_observation({**GOOD, "trees_surviving": 0}, "METH-003").is_valid


def test_surviving_equal_to_planted_is_allowed_boundary():
    assert validate_observation({**GOOD, "trees_surviving": 100}, "METH-003").is_valid


def test_surviving_above_planted_is_rejected():
    assert "INVALID_RELATION" in codes(validate_observation({**GOOD, "trees_surviving": 101}, "METH-003"))


def test_wrong_unit_is_flagged():
    obs = {**GOOD, "units": {"trees_planted": "kg"}}
    assert "INVALID_UNIT" in codes(validate_observation(obs, "METH-003"))


def test_correct_unit_is_accepted():
    obs = {**GOOD, "units": {"trees_planted": "count"}}
    assert validate_observation(obs, "METH-003").is_valid


def test_duplicate_observation_is_flagged():
    result = validate_observation(GOOD, "METH-003", known_observation_ids={"OBS-T1"})
    assert "DUPLICATE_OBSERVATION" in codes(result)


def test_missing_methodology_is_flagged():
    assert codes(validate_observation(GOOD, "METH-999")) == ["MISSING_METHODOLOGY"]


def test_incompatible_project_type_is_flagged():
    result = validate_observation({**GOOD, "project_type": "aquaculture"}, "METH-003")
    assert "INCOMPATIBLE_PROJECT_TYPE" in codes(result)


def test_missing_evidence_is_a_warning_not_an_error():
    obs = {k: v for k, v in GOOD.items() if k != "evidence_reference"}
    result = validate_observation(obs, "METH-003")
    assert result.is_valid
    assert [w.code for w in result.warnings] == ["MISSING_EVIDENCE"]