from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

import pandas as pd
import yaml

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT: Final[Path] = ROOT / "data/source_manifests/study_c_unit_weights.yml"
DEFAULT_PARTICIPATION: Final[Path] = ROOT / "data/private/fct/study_c_unit_participation.csv"
DEFAULT_CONCORDANCE: Final[Path] = ROOT / "data/private/fct/study_c_participant_dgeec_concordance.csv"
DEFAULT_EXPECTED: Final[Path] = ROOT / "data/private/fct/study_c_primary_units.csv"
DEFAULT_OUTPUT: Final[Path] = ROOT / "results/study_c/unit_institution_field_weights.csv"


def _load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path.name}: {missing}")
    return frame


def _normalise(value: str) -> str:
    return " ".join(value.strip().split())


def _parse_count(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    count = int(text)
    if count <= 0:
        raise ValueError("integrated_researcher_count must be positive when present")
    return count


def _load_unit_fields(expected_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(expected_path, dtype=str, keep_default_na=False)
    required = ["unit_reference", "isced_f_scope"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(
            "Primary-unit registry must include canonical unit_reference and isced_f_scope before weights "
            f"can be built; missing={missing}"
        )
    frame = frame[required].copy()
    frame["unit_reference"] = frame["unit_reference"].map(_normalise)
    frame["isced_f_scope"] = frame["isced_f_scope"].map(_normalise)
    if frame["unit_reference"].duplicated().any():
        raise ValueError("Primary-unit registry contains duplicate unit_reference values")
    if not set(frame["isced_f_scope"]) <= {"05", "06", "07"}:
        raise ValueError("Primary-unit registry contains fields outside frozen 05/06/07 scope")
    return frame


def build_weights(
    contract_path: Path,
    participation_path: Path,
    concordance_path: Path,
    expected_path: Path,
) -> pd.DataFrame:
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    participation_required = [
        "unit_reference",
        "participant_institution_id",
        "participant_institution_name",
        "integrated_researcher_count",
        "source_reference",
    ]
    participation = _load_csv(participation_path, participation_required).copy()
    concordance = _load_csv(
        concordance_path,
        list(contract["concordance_required_columns"]),
    ).copy()
    unit_fields = _load_unit_fields(expected_path)

    for column in ["unit_reference", "participant_institution_id", "participant_institution_name"]:
        participation[column] = participation[column].map(_normalise)
    for column in contract["concordance_required_columns"]:
        concordance[column] = concordance[column].map(_normalise)

    if participation.duplicated(["unit_reference", "participant_institution_id"]).any():
        raise ValueError("Participation input contains duplicate unit-participant rows")
    if concordance["participant_institution_id"].duplicated().any():
        raise ValueError("Concordance must map each participant_institution_id exactly once")

    joined = participation.merge(
        concordance,
        on=["participant_institution_id", "participant_institution_name"],
        how="left",
        validate="many_to_one",
        suffixes=("_participation", "_concordance"),
    )
    if (joined["dgeec_institution_code"].fillna("") == "").any():
        missing_ids = sorted(
            joined.loc[
                joined["dgeec_institution_code"].fillna("") == "",
                "participant_institution_id",
            ].unique()
        )
        raise ValueError(f"Missing participant→DGEEC concordance: {missing_ids[:10]}")

    joined = joined.merge(unit_fields, on="unit_reference", how="left", validate="many_to_one")
    if joined["isced_f_scope"].isna().any():
        raise ValueError("Participation contains units absent from frozen primary-unit registry")

    output_rows: list[dict[str, str | float]] = []
    for unit_reference, group in joined.groupby("unit_reference", sort=True):
        counts = [_parse_count(value) for value in group["integrated_researcher_count"]]
        present = [value is not None for value in counts]
        if any(present) and not all(present):
            raise ValueError(f"Mixed count availability for {unit_reference}")

        if all(present):
            numeric_counts = [int(value) for value in counts if value is not None]
            total = sum(numeric_counts)
            weights = [value / total for value in numeric_counts]
            basis = "count_derived"
        else:
            n = len(group)
            weights = [1.0 / n] * n
            basis = "equal_share"

        for (_, row), weight in zip(group.iterrows(), weights, strict=True):
            output_rows.append(
                {
                    "unit_reference": unit_reference,
                    "participant_institution_id": row["participant_institution_id"],
                    "dgeec_institution_code": row["dgeec_institution_code"],
                    "isced_f_scope": row["isced_f_scope"],
                    "weight": weight,
                    "weight_basis": basis,
                    "source_reference": row["source_reference_participation"],
                }
            )

    output = pd.DataFrame(output_rows)
    tolerance = float(contract["rules"]["tolerance"])
    sums = output.groupby("unit_reference")["weight"].sum()
    bad = sums[(sums - 1.0).abs() > tolerance]
    if not bad.empty:
        raise ValueError(f"Unit weights do not sum to one: {bad.to_dict()}")
    return output.sort_values(["unit_reference", "participant_institution_id"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--participation", type=Path, default=DEFAULT_PARTICIPATION)
    parser.add_argument("--concordance", type=Path, default=DEFAULT_CONCORDANCE)
    parser.add_argument("--expected-units", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        output = build_weights(
            args.contract,
            args.participation,
            args.concordance,
            args.expected_units,
        )
    except FileNotFoundError as exc:
        print(f"blocked_missing_private_input: {exc}")
        raise SystemExit(2) from exc

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(
        f"unit_weights_validated: units={output['unit_reference'].nunique()} "
        f"rows={len(output)} output={args.output}"
    )


if __name__ == "__main__":
    main()
