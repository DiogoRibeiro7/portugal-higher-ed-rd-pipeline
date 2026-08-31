from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/study_c/source_coverage_audit.yml"


def _audit() -> dict:
    return yaml.safe_load(AUDIT.read_text(encoding="utf-8"))


def test_study_c_coverage_gate_remains_closed_while_blockers_exist() -> None:
    audit = _audit()
    assert audit["unit_exposure_allowed"] is False
    blockers = audit["blockers_before_unit_exposure"]
    assert blockers
    assert "canonical_fct_final_results_file_not_retrieved" in blockers
    assert "institution_field_component_coverage_not_computed" in blockers


def test_publication_existence_is_not_treated_as_analysis_ready_coverage() -> None:
    audit = _audit()
    raides = audit["raides"]
    assert raides["official_annual_inscritos_tables_exist"] is True
    assert raides["official_annual_diplomados_tables_exist"] is True
    assert raides["institution_field_cycle_schema_full_window_verified"] is False
    assert raides["institution_field_component_coverage_computable"] is False


def test_ipctn_remains_context_only_until_granularity_is_verified() -> None:
    audit = _audit()
    ipctn = audit["ipctn"]
    assert ipctn["official_2024_definitive_results_identified"] is True
    assert ipctn["research_personnel_fte_context_identified"] is True
    assert ipctn["institution_scientific_field_schema_full_window_verified"] is False
    assert ipctn["contextual_unit_linkage_computable"] is False


def test_no_top_down_allocation_is_allowed() -> None:
    rules = _audit()["rules"]
    assert rules["national_or_sector_totals_may_not_be_allocated_to_units"] is True
    assert rules["search_snippets_may_not_define_registry_or_coverage"] is True
    assert rules["unavailable_dimensions_remain_unavailable"] is True
    assert rules["exposure_calculation_before_blockers_resolved"] is False
