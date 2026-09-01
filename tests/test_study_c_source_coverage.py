from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/study_c/source_coverage_audit.yml"
RAIDES_SCHEMA = ROOT / "data/source_manifests/study_c_raides_schema.yml"
SUPPORT_AUDIT = ROOT / "results/study_c/raides_support_audit.yml"


def _audit() -> dict:
    return yaml.safe_load(AUDIT.read_text(encoding="utf-8"))


def _support_audit() -> dict:
    return yaml.safe_load(SUPPORT_AUDIT.read_text(encoding="utf-8"))


def test_study_c_gate_has_only_fct_weight_blockers_remaining() -> None:
    audit = _audit()
    assert audit["unit_exposure_allowed"] is False
    assert audit["primary_blockers_before_unit_exposure"] == [
        "formal_unit_institution_participation_not_resolved",
        "unit_institution_field_weights_not_built",
    ]


def test_raides_full_window_support_gate_is_complete() -> None:
    audit = _audit()
    raides = audit["raides"]
    assert raides["official_annual_inscritos_tables_exist"] is True
    assert raides["official_annual_diplomados_tables_exist"] is True
    assert raides["component_semantics_resolved"] is True
    assert raides["official_file_bytes_validated_full_window"] is True
    assert raides["institution_course_field_cycle_schema_full_window_verified"] is True
    assert raides["institution_code_concordance_finalised"] is True
    assert raides["institution_field_component_coverage_computable"] is True
    assert raides["institution_field_component_coverage_computed"] is True
    assert raides["support_summary"]["eligible_series_minimum_five_years"] == 363
    assert raides["support_summary"]["pairs_all_five_components_eligible"] == 31


def test_raides_support_audit_preserves_missing_not_zero_rule() -> None:
    support = _support_audit()
    assert support["summary"]["institution_field_component_series"] == 494
    assert support["summary"]["institution_field_pairs"] == 160
    assert support["summary"]["institution_codes"] == 74
    assert support["summary"]["codes_in_both_raides_families"] == 69
    assert support["support_rule"]["minimum_comparable_annual_observations"] == 5
    assert support["support_rule"]["year_is_supported_only_when_actual_record_exists"] is True
    assert support["support_rule"]["absent_row_is_not_promoted_to_zero"] is True
    assert support["unit_exposure_allowed"] is False


def test_raides_schema_keeps_five_registered_components_separate() -> None:
    schema = yaml.safe_load(RAIDES_SCHEMA.read_text(encoding="utf-8"))
    components = schema["component_contract"]
    assert list(components) == [
        "first_time_entrants",
        "graduates_first_cycle",
        "graduates_second_cycle",
        "doctoral_enrolments",
        "doctoral_graduates",
    ]
    assert all(c["status"] == "semantic_and_file_schema_validated" for c in components.values())
    assert schema["aggregation_rules"]["allocate_national_totals_downwards"] is False
    assert schema["aggregation_rules"]["allocate_sector_totals_downwards"] is False
    assert schema["aggregation_rules"]["minimum_comparable_annual_observations"] == 5


def test_fct_registry_and_ratings_are_available_but_weights_are_not() -> None:
    fct = _audit()["fct"]
    assert fct["approved_units_total"] == 313
    assert fct["unit_registry_available"] is True
    assert fct["rating_complete_for_approved_units"] is True
    assert fct["institution_mapping_auditable_from_final_results_file"] is False
    assert fct["unit_weights_auditable"] is False


def test_unit_weight_gate_is_executable_but_not_run_without_private_handoff() -> None:
    gate = _audit()["fct"]["unit_weight_gate"]
    assert gate["deterministic_weight_builder_available"] is True
    assert gate["participant_dgeec_concordance_required"] is True
    assert gate["output_built"] is False
    assert gate["sum_to_one_validation_required"] is True
    assert gate["missing_raides_support_may_trigger_weight_renormalisation"] is False


def test_ipctn_is_context_only_and_does_not_block_primary_feeder_exposure() -> None:
    audit = _audit()
    ipctn = audit["ipctn"]
    assert ipctn["role"] == "context_only_not_primary_feeder_gate"
    assert ipctn["omission_blocks_primary_feeder_exposure"] is False
    assert "ipctn_institution_field_fte_schema_not_verified_for_full_window" in audit[
        "context_only_limitations"
    ]
    assert "ipctn_institution_field_fte_schema_not_verified_for_full_window" not in audit[
        "primary_blockers_before_unit_exposure"
    ]


def test_no_top_down_allocation_is_allowed() -> None:
    rules = _audit()["rules"]
    assert rules["national_or_sector_totals_may_not_be_allocated_to_units"] is True
    assert rules["search_snippets_may_not_define_registry_or_coverage"] is True
    assert rules["unavailable_dimensions_remain_unavailable"] is True
    assert rules["exposure_calculation_before_primary_blockers_resolved"] is False
    assert (
        rules[
            "formal_participant_weights_may_not_be_renormalised_around_missing_raides_support"
        ]
        is True
    )
