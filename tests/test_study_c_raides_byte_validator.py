from pathlib import Path

import yaml

from scripts.validate_study_c_raides_files import validate

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "data/source_manifests/study_c_raides_file_inventory.yml"


def test_validator_fails_closed_without_author_supplied_files(tmp_path: Path) -> None:
    result = validate(INVENTORY, tmp_path)
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert result["status"] == "blocked_missing_files"
    assert result["expected_files"] == 14
    assert result["validated_files"] == 0
    assert len(result["missing"]) == 14
    assert result["endpoint_schema_comparable"] is False
    assert result["full_window_schema_validated"] is False
    assert inventory["expected_annual_file_count"] == 14


def test_inventory_contains_exact_two_families_across_seven_years() -> None:
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert inventory["families"] == ["inscritos", "diplomados"]
    years = [
        "2018/19",
        "2019/20",
        "2020/21",
        "2021/22",
        "2022/23",
        "2023/24",
        "2024/25",
    ]
    slots = {(x["academic_year"], x["family"]) for x in inventory["annual_files"]}
    assert slots == {(year, family) for year in years for family in inventory["families"]}


def test_schema_validation_cannot_be_declared_from_publication_discovery() -> None:
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert inventory["byte_validation"]["retrieved_annual_files"] == 0
    assert inventory["byte_validation"]["endpoint_schema_compared"] is False
    assert inventory["byte_validation"]["full_window_schema_compared"] is False
