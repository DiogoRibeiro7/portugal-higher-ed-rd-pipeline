from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_study_c_source_manifest_preserves_manual_fct_dependency() -> None:
    manifest = yaml.safe_load(
        (ROOT / "data/source_manifests/study_c_sources.yml").read_text(encoding="utf-8")
    )
    fct = manifest["sources"]["fct_evaluation_2023_2024"]
    assert fct["canonical_file_required_before_unit_results"] is True
    assert fct["retrieval_mode"] == "manual_author_supplied_required"
    assert fct["use_as_downstream_outcome"] is False
    assert manifest["rules"]["search_snippets_as_data"] is False
    assert manifest["rules"]["compute_unit_exposure_before_all_required_sources_resolved"] is False


def test_panel_crosswalk_is_restricted_to_frozen_study_c_fields() -> None:
    crosswalk = pd.read_csv(
        ROOT / "data/curated/fct/study_c_panel_isced_crosswalk.csv",
        dtype={"isced_f_scope": str},
    )
    primary = crosswalk.loc[crosswalk["primary_study_c_scope"].astype(bool)]
    assert not primary.empty
    assert set(primary["isced_f_scope"]) <= {"05", "06", "07"}
    assert primary["panel_key"].is_unique


def test_raides_contract_keeps_pipeline_components_separate() -> None:
    manifest = yaml.safe_load(
        (ROOT / "data/source_manifests/study_c_sources.yml").read_text(encoding="utf-8")
    )
    required = manifest["sources"]["raides"]["required_components"]
    assert required == [
        "first_time_entrants",
        "graduates_first_cycle",
        "graduates_second_cycle",
        "doctoral_enrolments",
        "doctoral_graduates",
    ]
    assert "research_personnel_fte" not in required


def test_ipctn_fte_is_context_only() -> None:
    manifest = yaml.safe_load(
        (ROOT / "data/source_manifests/study_c_sources.yml").read_text(encoding="utf-8")
    )
    ipctn = manifest["sources"]["ipctn"]
    assert ipctn["required_measure"] == "research_personnel_fte"
    assert ipctn["role"] == "context_only_not_feeder_composite"
