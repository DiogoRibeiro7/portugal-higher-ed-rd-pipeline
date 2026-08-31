from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/study_c/source_coverage_audit.yml"
RAIDES_SCHEMA = ROOT / "data/source_manifests/study_c_raides_schema.yml"


def _audit() -> dict:
    return yaml.safe_load(AUDIT.read_text(encoding="utf-8"))


def test_study_c_coverage_gate_remains_closed_while_primary_blockers_exist() -> None:
    audit = _audit()
    assert audit["unit_exposure_allowed"] is False
    blockers = audit["primary_blockers_before_unit_exposure"]
    assert blockers
    assert "canonical_fct_final_results_file_not_retrieved" in blockers
    assert "raides_official_file_bytes_not_validated_for_full_window" in blockers
    assert "institution_field_component_coverage_not_computed" in blockers


def test_raides_semantics_are_resolved_but_file_validation_is_still_pending() -> None:
    audit = _audit()
    raides = audit["raides"]
    assert raides["official_annual_inscritos_tables_exist"] is True
    assert raides["official_annual_diplomados_tables_exist"] is True
    assert raides["component_semantics_resolved"] is True
    assert raides["official_file_bytes_validated_full_window"] is False
    assert raides["institution_field_component_coverage_computable"] is False


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
    assert schema["aggregation_rules"]["allocate_national_totals_downwards"] is False
    assert schema["aggregation_rules"]["allocate_sector_totals_downwards"] is False
    assert schema["aggregation_rules"]["minimum_comparable_annual_observations"] == 5


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
