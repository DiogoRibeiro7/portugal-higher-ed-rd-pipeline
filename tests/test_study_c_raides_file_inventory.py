from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data/source_manifests/study_c_raides_file_inventory.yml"


def _inventory() -> dict:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))


def test_raides_inventory_freezes_all_seven_years_and_fourteen_annual_files() -> None:
    inv = _inventory()
    years = inv["frozen_window"]["academic_years"]
    assert years == [
        "2018/19",
        "2019/20",
        "2020/21",
        "2021/22",
        "2022/23",
        "2023/24",
        "2024/25",
    ]
    assert inv["annual_publication_families"]["inscritos"]["expected_files"] == 7
    assert inv["annual_publication_families"]["diplomados"]["expected_files"] == 7
    assert inv["byte_level_validation"]["total_expected_annual_files"] == 14


def test_publication_inventory_records_completed_file_byte_validation() -> None:
    inv = _inventory()
    families = inv["annual_publication_families"]
    assert families["inscritos"]["publication_entries_verified"] == 7
    assert families["diplomados"]["publication_entries_verified"] == 7
    assert families["inscritos"]["actual_spreadsheet_payloads_retrieved"] is True
    assert families["diplomados"]["actual_spreadsheet_payloads_retrieved"] is True
    assert inv["byte_level_validation"]["total_retrieved_annual_files"] == 14
    assert inv["byte_level_validation"]["full_two_family_window_schema_compared"] is True


def test_first_time_entry_series_is_available_from_inscritos_field() -> None:
    series = _inventory()["first_time_entry_series"]
    assert series["official_series_identified"] is True
    assert series["published_span"] == "2012/13-2024/25"
    assert series["institution_course_granularity_stated_by_dgeec"] is True
    assert series["annual_inscritos_field_primeira_vez_available_in_frozen_window"] is True


def test_raides_support_gate_is_complete_but_unit_exposure_remains_closed() -> None:
    inv = _inventory()
    validation = inv["byte_level_validation"]
    assert validation["inscritos_endpoint_schema_compared"] is True
    assert validation["five_year_institution_field_component_support_computable"] is True
    assert inv["rules"]["publication_listing_is_not_byte_validation"] is True
    assert inv["rules"]["unit_exposure_allowed_from_raides_before_support_audit"] is False
