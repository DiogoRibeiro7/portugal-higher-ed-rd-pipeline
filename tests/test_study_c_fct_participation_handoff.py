from pathlib import Path

import pandas as pd
import pytest
import yaml

from scripts.validate_study_c_fct_participation import validate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data/source_manifests/study_c_fct_participation.yml"
SOURCE_AUDIT = ROOT / "results/study_c/source_coverage_audit.yml"


def _expected_units() -> list[str]:
    return [f"UID/{unit_id:05d}/2023" for unit_id in range(1, 121)]


def _write_expected_units(path: Path) -> None:
    pd.DataFrame({"unit_reference": _expected_units()}).to_csv(path, index=False)


def _base_participation() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "unit_reference": unit_reference,
                "participant_institution_id": f"ORG-{index:03d}",
                "participant_institution_name": f"Institution {index}",
                "source_system": "pct_evaluation_application_export",
                "source_record_id": f"record-{index}",
                "snapshot_basis": "submitted_evaluation_2023_2024_application",
                "integrated_researcher_count": "",
                "source_reference": f"pct-export:{index}",
            }
            for index, unit_reference in enumerate(_expected_units(), start=1)
        ]
    )


def test_handoff_contract_preserves_fail_closed_source_boundary() -> None:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    source = contract["source_boundary"]
    assert source["public_fct"]["public_results_resolve_complete_formal_participant_universe"] is False
    assert source["public_fct"]["may_close_formal_participation_gate"] is False
    assert source["authorised_participation_source"]["application_snapshot_required"] is True
    assert contract["weight_preparation"]["management_only_rows_as_substitute_for_participants"] is False
    assert contract["scientific_boundary"]["no_unit_exposure_computed"] is True


def test_master_source_audit_records_handoff_without_opening_gate() -> None:
    audit = yaml.safe_load(SOURCE_AUDIT.read_text(encoding="utf-8"))
    participation = audit["fct"]["organisational_participation"]
    assert participation["public_fct_evaluation_process_identified"] is True
    assert participation["public_results_complete_formal_participant_universe"] is False
    assert participation["authorised_application_snapshot_required"] is True
    assert participation["handoff_validated"] is False
    assert audit["unit_exposure_allowed"] is False
    assert audit["primary_blockers_before_unit_exposure"] == [
        "formal_unit_institution_participation_not_resolved",
        "unit_institution_field_weights_not_built",
    ]


def test_missing_authorised_export_keeps_participation_gate_closed(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    _write_expected_units(expected)

    result = validate(CONTRACT, tmp_path / "missing.csv", expected)

    assert result["status"] == "blocked_missing_authorised_participation_export"
    assert result["validated_primary_units"] == 0
    assert result["formal_participation_resolved"] is False
    assert result["unit_weights_ready"] is False


def test_complete_formal_participation_handoff_validates_without_building_weights(
    tmp_path: Path,
) -> None:
    expected = tmp_path / "expected.csv"
    participation = tmp_path / "participation.csv"
    _write_expected_units(expected)

    frame = _base_participation()
    first = frame.iloc[[0]].copy()
    first["participant_institution_id"] = "ORG-001-B"
    first["participant_institution_name"] = "Institution 1B"
    first["source_record_id"] = "record-1-b"
    first["source_reference"] = "pct-export:1-b"
    frame.loc[frame["unit_reference"] == "UID/00001/2023", "integrated_researcher_count"] = "12"
    first["integrated_researcher_count"] = "8"
    frame = pd.concat([frame, first], ignore_index=True)
    frame.to_csv(participation, index=False)

    result = validate(CONTRACT, participation, expected)

    assert result["status"] == "formal_participation_handoff_validated_weights_pending"
    assert result["validated_primary_units"] == 120
    assert result["participation_rows"] == 121
    assert result["formal_participation_resolved"] is True
    assert result["unit_weights_ready"] is False
    assert result["weight_basis_units"] == {"count_derived": 1, "equal_share": 119}
    assert result["next_gate"] == "build_canonical_unit_institution_field_weights"


def test_partial_counts_within_unit_are_rejected(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    participation = tmp_path / "participation.csv"
    _write_expected_units(expected)

    frame = _base_participation()
    first = frame.iloc[[0]].copy()
    first["participant_institution_id"] = "ORG-001-B"
    first["participant_institution_name"] = "Institution 1B"
    first["source_record_id"] = "record-1-b"
    first["source_reference"] = "pct-export:1-b"
    frame.loc[frame["unit_reference"] == "UID/00001/2023", "integrated_researcher_count"] = "12"
    frame = pd.concat([frame, first], ignore_index=True)
    frame.to_csv(participation, index=False)

    with pytest.raises(ValueError, match="Mixed integrated-researcher count availability"):
        validate(CONTRACT, participation, expected)


def test_current_membership_snapshot_is_rejected(tmp_path: Path) -> None:
    expected = tmp_path / "expected.csv"
    participation = tmp_path / "participation.csv"
    _write_expected_units(expected)

    frame = _base_participation()
    frame["snapshot_basis"] = "current_membership_2026"
    frame.to_csv(participation, index=False)

    with pytest.raises(ValueError, match="submitted_evaluation_2023_2024_application"):
        validate(CONTRACT, participation, expected)
