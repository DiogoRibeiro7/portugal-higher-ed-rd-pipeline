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


def test_panel_crosswalk_uses_exact_fct_panel_universe_and_frozen_fields() -> None:
    crosswalk = pd.read_csv(
        ROOT / "data/curated/fct/study_c_panel_isced_crosswalk.csv",
        dtype={"isced_f_scope": str},
    )
    assert len(crosswalk) == 29
    assert crosswalk["panel_key"].is_unique
    assert crosswalk["panel_label"].is_unique

    required_labels = {
        "Earth and Environmental Sciences and Technologies",
        "Materials Science and Engineering, and Nanotechnology",
        "Mechanical Engineering and Engineering systems",
        "Civil and Geological engineering",
        "Chemical and Biological Engineering",
        "Chemistry",
        "Computer Science and Information Technologies",
        "Architecture and Urbanism",
        "Biological Sciences Biodiversity and Ecosystems",
        "Electrical and Computer Engineering",
        "Mathematics",
        "Physics",
    }
    assert required_labels <= set(crosswalk["panel_label"])

    primary = crosswalk.loc[crosswalk["primary_study_c_scope"].astype(bool)]
    assert len(primary) == 12
    assert set(primary["isced_f_scope"]) <= {"05", "06", "07"}
    assert set(primary["panel_label"]) == required_labels


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
