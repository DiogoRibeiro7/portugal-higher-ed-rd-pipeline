from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from scripts.build_study_c_unit_weights import build_weights

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/source_manifests/study_c_unit_weights.yml"


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    participation = pd.DataFrame(
        [
            {
                "unit_reference": "UID/00001/2023",
                "participant_institution_id": "PTCRIS:A",
                "participant_institution_name": "Institution A",
                "integrated_researcher_count": "3",
                "source_reference": "record:a",
            },
            {
                "unit_reference": "UID/00001/2023",
                "participant_institution_id": "PTCRIS:B",
                "participant_institution_name": "Institution B",
                "integrated_researcher_count": "1",
                "source_reference": "record:b",
            },
            {
                "unit_reference": "UID/00002/2023",
                "participant_institution_id": "PTCRIS:C",
                "participant_institution_name": "Institution C",
                "integrated_researcher_count": "",
                "source_reference": "record:c",
            },
            {
                "unit_reference": "UID/00002/2023",
                "participant_institution_id": "PTCRIS:D",
                "participant_institution_name": "Institution D",
                "integrated_researcher_count": "",
                "source_reference": "record:d",
            },
        ]
    )
    concordance = pd.DataFrame(
        [
            ["PTCRIS:A", "Institution A", "1001", "DGEEC A", "manual_review", "ref:a"],
            ["PTCRIS:B", "Institution B", "1002", "DGEEC B", "manual_review", "ref:b"],
            ["PTCRIS:C", "Institution C", "1003", "DGEEC C", "manual_review", "ref:c"],
            ["PTCRIS:D", "Institution D", "1004", "DGEEC D", "manual_review", "ref:d"],
        ],
        columns=[
            "participant_institution_id",
            "participant_institution_name",
            "dgeec_institution_code",
            "dgeec_institution_name",
            "mapping_basis",
            "source_reference",
        ],
    )
    expected = pd.DataFrame(
        [
            {"unit_reference": "UID/00001/2023", "panel_label": "Chemistry"},
            {
                "unit_reference": "UID/00002/2023",
                "panel_label": "Mechanical Engineering and Engineering Systems",
            },
        ]
    )
    crosswalk = pd.DataFrame(
        [
            {"panel_label": "Chemistry", "isced_f_scope": "05", "primary_study_c_scope": "true"},
            {
                "panel_label": "Mechanical Engineering and Engineering Systems",
                "isced_f_scope": "07",
                "primary_study_c_scope": "true",
            },
            {"panel_label": "Psychology", "isced_f_scope": "", "primary_study_c_scope": "false"},
        ]
    )

    participation_path = tmp_path / "participation.csv"
    concordance_path = tmp_path / "concordance.csv"
    expected_path = tmp_path / "expected.csv"
    crosswalk_path = tmp_path / "crosswalk.csv"
    participation.to_csv(participation_path, index=False)
    concordance.to_csv(concordance_path, index=False)
    expected.to_csv(expected_path, index=False)
    crosswalk.to_csv(crosswalk_path, index=False)
    return participation_path, concordance_path, expected_path, crosswalk_path


def test_weight_gate_contract_preserves_fail_closed_rules() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    rules = contract["rules"]
    assert rules["canonical_join_key"] == "participant_institution_id"
    assert rules["participant_names_are_audit_labels_not_join_keys"] is True
    assert rules["fuzzy_name_matching_in_production"] is False
    assert rules["dgeec_code_required_for_every_participant"] is True
    assert rules["panel_field_source"] == "canonical_fct_panel_crosswalk"
    assert rules["staged_unit_registry_carries_panel_label_not_isced_scope"] is True
    assert rules["weights_sum_to_one_per_unit"] is True
    assert rules["participant_rows_may_not_be_dropped_for_missing_raides_support"] is True
    assert rules["unsupported_institution_field_pairs_remain_unavailable_later"] is True


def test_build_weights_uses_registered_count_equal_share_and_crosswalk_rules(
    tmp_path: Path,
) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    output = build_weights(CONTRACT, participation, concordance, expected, crosswalk)

    first = output.loc[output["unit_reference"] == "UID/00001/2023"]
    assert first["weight_basis"].unique().tolist() == ["count_derived"]
    assert first["weight"].tolist() == [0.75, 0.25]

    second = output.loc[output["unit_reference"] == "UID/00002/2023"]
    assert second["weight_basis"].unique().tolist() == ["equal_share"]
    assert second["weight"].tolist() == [0.5, 0.5]

    sums = output.groupby("unit_reference")["weight"].sum()
    assert (sums == 1.0).all()
    assert set(output["isced_f_scope"]) == {"05", "07"}


def test_build_weights_joins_concordance_by_id_when_names_differ(tmp_path: Path) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    frame = pd.read_csv(concordance, dtype=str, keep_default_na=False)
    frame.loc[
        frame["participant_institution_id"] == "PTCRIS:A", "participant_institution_name"
    ] = "Institution A legal name"
    frame.to_csv(concordance, index=False)

    output = build_weights(CONTRACT, participation, concordance, expected, crosswalk)
    row = output.loc[output["participant_institution_id"] == "PTCRIS:A"].iloc[0]

    assert row["dgeec_institution_code"] == "1001"
    assert row["participant_institution_name"] == "Institution A"
    assert row["concordance_participant_institution_name"] == "Institution A legal name"


def test_build_weights_fails_when_participant_has_no_dgeec_mapping(tmp_path: Path) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    frame = pd.read_csv(concordance, dtype=str)
    frame = frame.loc[frame["participant_institution_id"] != "PTCRIS:B"]
    frame.to_csv(concordance, index=False)

    with pytest.raises(ValueError, match="Missing participant→DGEEC concordance"):
        build_weights(CONTRACT, participation, concordance, expected, crosswalk)


def test_build_weights_rejects_partial_researcher_counts(tmp_path: Path) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    frame = pd.read_csv(participation, dtype=str, keep_default_na=False)
    frame.loc[
        frame["participant_institution_id"] == "PTCRIS:D",
        "integrated_researcher_count",
    ] = "2"
    frame.to_csv(participation, index=False)

    with pytest.raises(ValueError, match="Mixed count availability"):
        build_weights(CONTRACT, participation, concordance, expected, crosswalk)


def test_primary_unit_registry_must_carry_canonical_panel_label(tmp_path: Path) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    frame = pd.read_csv(expected, dtype=str).drop(columns=["panel_label"])
    frame.to_csv(expected, index=False)

    with pytest.raises(ValueError, match="panel_label"):
        build_weights(CONTRACT, participation, concordance, expected, crosswalk)


def test_primary_unit_panel_must_exist_in_canonical_primary_crosswalk(tmp_path: Path) -> None:
    participation, concordance, expected, crosswalk = _write_inputs(tmp_path)
    frame = pd.read_csv(expected, dtype=str, keep_default_na=False)
    frame.loc[frame["unit_reference"] == "UID/00001/2023", "panel_label"] = "Psychology"
    frame.to_csv(expected, index=False)

    with pytest.raises(ValueError, match="canonical primary crosswalk"):
        build_weights(CONTRACT, participation, concordance, expected, crosswalk)
