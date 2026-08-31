from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "data/source_manifests/study_c_fct_participation.yml"
DEFAULT_EXPECTED = ROOT / "data/private/fct/study_c_primary_units.csv"
DEFAULT_PARTICIPATION = ROOT / "data/private/fct/study_c_unit_participation.csv"
UNIT_REFERENCE_RE = re.compile(r"^UID/\d{5}/2023$")


def _load_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in required_columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path.name}: {missing}")
    return frame


def _normalise_text(value: str) -> str:
    return " ".join(value.strip().split())


def _validate_expected_units(frame: pd.DataFrame, expected_total: int) -> set[str]:
    refs = [_normalise_text(value) for value in frame["unit_reference"].tolist()]
    if len(refs) != expected_total:
        raise ValueError(f"Expected {expected_total} primary-scope units, found {len(refs)}")
    if len(set(refs)) != expected_total:
        raise ValueError("Expected-unit file contains duplicate unit references")
    invalid = sorted(ref for ref in refs if UNIT_REFERENCE_RE.fullmatch(ref) is None)
    if invalid:
        raise ValueError(f"Invalid canonical unit references: {invalid[:5]}")
    return set(refs)


def _parse_positive_count(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        parsed = int(text)
    except ValueError as exc:
        raise ValueError(f"Integrated researcher count is not an integer: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"Integrated researcher count must be positive: {parsed}")
    return parsed


def validate(contract_path: Path, participation_path: Path, expected_path: Path) -> dict[str, Any]:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    expected_required = contract["handoff"]["expected_units_required_columns"]
    participation_required = contract["handoff"]["participation_required_columns"]
    expected_total = int(contract["scope"]["primary_scope_units"])

    if not participation_path.exists():
        return {
            "status": "blocked_missing_authorised_participation_export",
            "validated_primary_units": 0,
            "formal_participation_resolved": False,
            "unit_weights_ready": False,
        }
    if not expected_path.exists():
        return {
            "status": "blocked_missing_primary_scope_unit_registry",
            "validated_primary_units": 0,
            "formal_participation_resolved": False,
            "unit_weights_ready": False,
        }

    expected = _load_csv(expected_path, expected_required)
    expected_refs = _validate_expected_units(expected, expected_total)
    frame = _load_csv(participation_path, participation_required).copy()

    for column in participation_required:
        if column == "integrated_researcher_count":
            continue
        frame[column] = frame[column].map(_normalise_text)
        if (frame[column] == "").any():
            raise ValueError(f"Blank values are not allowed in required column {column!r}")

    if frame.empty:
        raise ValueError("Participation handoff is empty")

    invalid_refs = sorted(
        ref for ref in frame["unit_reference"].unique() if UNIT_REFERENCE_RE.fullmatch(ref) is None
    )
    if invalid_refs:
        raise ValueError(f"Invalid participation unit references: {invalid_refs[:5]}")

    observed_refs = set(frame["unit_reference"])
    missing_units = sorted(expected_refs - observed_refs)
    extra_units = sorted(observed_refs - expected_refs)
    if missing_units or extra_units:
        raise ValueError(
            "Participation handoff does not match frozen primary scope: "
            f"missing={missing_units[:5]}, extra={extra_units[:5]}"
        )

    expected_snapshot = contract["handoff"]["required_snapshot_basis"]
    snapshots = set(frame["snapshot_basis"])
    if snapshots != {expected_snapshot}:
        raise ValueError(
            f"Participation export must use snapshot {expected_snapshot!r}; found {sorted(snapshots)}"
        )

    duplicate_key = frame.duplicated(["unit_reference", "participant_institution_id"])
    if duplicate_key.any():
        duplicates = frame.loc[
            duplicate_key, ["unit_reference", "participant_institution_id"]
        ].to_dict("records")
        raise ValueError(f"Duplicate unit-participant rows found: {duplicates[:5]}")

    count_modes: dict[str, str] = {}
    participant_counts: dict[str, int] = {}
    for unit_reference, group in frame.groupby("unit_reference", sort=True):
        parsed = [_parse_positive_count(value) for value in group["integrated_researcher_count"]]
        present = [value is not None for value in parsed]
        if any(present) and not all(present):
            raise ValueError(
                f"Mixed integrated-researcher count availability for {unit_reference}; "
                "counts must be complete or entirely absent within a unit"
            )
        count_modes[unit_reference] = "count_derived" if all(present) else "equal_share"
        participant_counts[unit_reference] = len(group)

    return {
        "status": "formal_participation_handoff_validated_weights_pending",
        "validated_primary_units": len(observed_refs),
        "participation_rows": len(frame),
        "formal_participation_resolved": True,
        "unit_weights_ready": False,
        "weight_basis_units": {
            "count_derived": sum(mode == "count_derived" for mode in count_modes.values()),
            "equal_share": sum(mode == "equal_share" for mode in count_modes.values()),
        },
        "participant_count_summary": {
            "minimum": min(participant_counts.values()),
            "maximum": max(participant_counts.values()),
        },
        "next_gate": "build_canonical_unit_institution_field_weights",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("participation_csv", nargs="?", type=Path, default=DEFAULT_PARTICIPATION)
    parser.add_argument("--expected-units", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = validate(args.contract, args.participation_csv, args.expected_units)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if result["formal_participation_resolved"] is False:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
