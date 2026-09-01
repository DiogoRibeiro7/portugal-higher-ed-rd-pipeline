from pathlib import Path

import yaml

from scripts.validate_study_c_raides_files import annual_slots, validate

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data/source_manifests/study_c_raides_file_inventory.yml"


def _inventory() -> dict:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))


def test_validator_fails_closed_without_author_supplied_files(tmp_path: Path) -> None:
    result = validate(INVENTORY, tmp_path)
    assert result["status"] == "blocked_missing_files"
    assert result["expected_files"] == 14
    assert result["validated_files"] == 0
    assert len(result["missing"]) == 14
    assert result["endpoint_schema_comparable"] is False
    assert result["full_window_schema_validated"] is False


def test_real_inventory_resolves_exact_two_families_across_seven_years() -> None:
    inventory = _inventory()
    years = [
        "2018/19",
        "2019/20",
        "2020/21",
        "2021/22",
        "2022/23",
        "2023/24",
        "2024/25",
    ]
    assert inventory["frozen_window"]["academic_years"] == years
    assert set(inventory["annual_publication_families"]) == {"inscritos", "diplomados"}
    slots = annual_slots(inventory)
    assert len(slots) == 14
    assert {(x["academic_year"], x["family"]) for x in slots} == {
        (year, family)
        for year in years
        for family in ("inscritos", "diplomados")
    }


def test_canonical_staging_stems_are_deterministic_and_local() -> None:
    slots = annual_slots(_inventory())
    stems = {x["local_stem"] for x in slots}
    assert "inscritos_2018_19" in stems
    assert "diplomados_2024_25" in stems
    assert len(stems) == 14


def test_inventory_records_completed_byte_and_schema_validation() -> None:
    inventory = _inventory()
    byte_validation = inventory["byte_level_validation"]
    assert byte_validation["total_retrieved_annual_files"] == 14
    assert byte_validation["inscritos_endpoint_schema_compared"] is True
    assert byte_validation["full_two_family_window_schema_compared"] is True
    assert byte_validation["five_year_institution_field_component_support_computable"] is True
    assert inventory["rules"]["publication_listing_is_not_byte_validation"] is True


def test_inventory_and_validator_contract_are_end_to_end_compatible(tmp_path: Path) -> None:
    inventory = _inventory()
    slots = annual_slots(inventory)
    assert len(slots) == inventory["byte_level_validation"]["total_expected_annual_files"]
    result = validate(INVENTORY, tmp_path)
    assert result["expected_files"] == len(slots)
    assert {m["canonical_staging_stem"] for m in result["missing"]} == {
        s["local_stem"] for s in slots
    }
