from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "study_c.yml"


def _config() -> dict[str, object]:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def test_study_c_primary_phase_is_exposure_not_causal_outcome_analysis() -> None:
    config = _config()
    assert config["primary_estimand_type"] == "descriptive_exposure"
    assert config["causal_language_allowed"] is False

    fct = config["fct"]
    assert fct["rating_role"] == "stratifier_only"
    assert fct["rating_as_downstream_outcome_for_primary_window"] is False

    downstream = config["downstream_outcomes"]
    assert downstream["enabled_in_primary_phase"] is False
    assert downstream["require_strictly_post_exposure_outcome"] is True
    assert downstream["require_separate_prospective_design_freeze"] is True


def test_study_c_feeder_scope_and_support_are_frozen() -> None:
    config = _config()
    fields = config["fields"]
    assert fields["primary_isced_f_2013"] == ["05", "06", "07"]
    assert fields["ambiguous_panel_primary_inclusion"] is False

    pipeline = config["pipeline"]
    assert pipeline["minimum_comparable_annual_observations"] == 5
    assert pipeline["missing_imputation"] is False
    assert pipeline["zero_handling"] == "endpoint_and_linear_count_sensitivity_no_log_offset"
    assert pipeline["primary_components"] == [
        "first_time_entrants",
        "graduates_first_cycle",
        "graduates_second_cycle",
        "doctoral_enrolments",
        "doctoral_graduates",
    ]


def test_research_personnel_is_context_not_feeder_component() -> None:
    config = _config()
    research_personnel = config["research_personnel"]
    assert research_personnel["role"] == "contextual_end_stage_stock"
    assert research_personnel["included_in_feeder_composite"] is False

    assert "research_personnel_fte" not in config["pipeline"]["primary_components"]


def test_study_c_weights_cannot_be_inferred_from_outcomes() -> None:
    config = _config()
    weights = config["host_weights"]
    assert weights["required_sum"] == 1.0
    assert weights["infer_from_rankings"] is False
    assert weights["infer_from_admissions"] is False
    assert weights["infer_from_geographic_proximity"] is False


def test_study_c_reproducibility_gate_precedes_results() -> None:
    config = _config()
    required = config["reproducibility_gate"]["required_before_unit_level_results"]
    assert required == [
        "fct_unit_registry_and_rating_source_manifest",
        "fct_panel_to_isced_crosswalk",
        "unit_to_institution_weight_table",
        "raides_source_manifest_and_variable_contract",
        "ipctn_source_manifest_and_fte_contract",
        "institution_field_component_coverage_audit",
        "validation_tests",
    ]
