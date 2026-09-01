from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

import pandas as pd
import yaml

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT: Final[Path] = ROOT / "data/source_manifests/study_c_unit_weights.yml"
DEFAULT_PARTICIPATION: Final[Path] = (
    ROOT / "data/private/fct/study_c_unit_participation.csv"
)
DEFAULT_CONCORDANCE: Final[Path] = (
    ROOT / "data/private/fct/study_c_participant_dgeec_concordance.csv"
)
DEFAULT_EXPECTED: Final[Path] = ROOT / "data/private/fct/study_c_primary_units.csv"
DEFAULT_PANEL_CROSSWALK: Final[Path] = (
    ROOT / "data/curated/fct/study_c_panel_isced_crosswalk.csv"
)
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


def _load_unit_fields(expected_path: Path, panel_crosswalk_path: Path) -> pd.DataFrame:
    units = _load_csv(expected_path, ["unit_reference", "panel_label"])[
        ["unit_reference", "panel_label"]
    ].copy()
    units["unit_reference"] = units["unit_reference"].map(_normalise)
    units["panel_label"] = units["panel_label"].map(_normalise)
    if units["unit_reference"].duplicated().any():
        raise ValueError("Primary-unit registry contains duplicate unit_reference values")
    if (units["panel_label"] == "").any():
        raise ValueError("Primary-unit registry contains blank canonical panel labels")

    crosswalk = _load_csv(
        panel_crosswalk_path,
        ["panel_label", "isced_f_scope", "primary_study_c_scope"],
    )[["panel_label", "isced_f_scope", "primary_study_c_scope"]].copy()
    crosswalk["panel_label"] = crosswalk["panel_label"].map(_normalise)
    crosswalk["isced_f_scope"] = crosswalk["isced_f_scope"].map(_normalise)
    crosswalk["primary_study_c_scope"] = crosswalk["primary_study_c_scope"].map(
        lambda value: _normalise(value).lower()
    )
    if crosswalk["panel_label"].duplicated().any():
        raise ValueError("Canonical panel crosswalk contains duplicate panel labels")

    primary = crosswalk.loc[crosswalk["primary_study_c_scope"] == "true"].copy()
    if not set(primary["isced_f_scope"]) <= {"05", "06", "07"}:
        raise ValueError(
            "Canonical primary panel crosswalk contains fields outside frozen "
            "05/06/07 scope"
        )

    unit_fields = units.merge(
        primary[["panel_label", "isced_f_scope"]],
        on="panel_label",
        how="left",
        validate="many_to_one",
    )
    if unit_fields["isced_f_scope"].isna().any():
        missing_panels = sorted(
            unit_fields.loc[unit_fields["isced_f_scope"].isna(), "panel_label"].unique()
        )
        raise ValueError(
            "Primary-unit registry contains panel labels absent from the canonical "
            f"primary crosswalk: {missing_panels[:10]}"
        )
    return unit_fields[["unit_reference", "panel_label", "isced_f_scope"]]


def _validate_mapping_statuses(concordance: pd.DataFrame, contract: dict) -> None:
    allowed = set(contract["allowed_mapping_statuses"])
    invalid = sorted(set(concordance["mapping_status"]) - allowed)
    if invalid:
        raise ValueError(f"Unsupported participant mapping_status values: {invalid}")

    mapped = concordance["mapping_status"] == "mapped_to_dgeec_establishment"
    non_he = concordance["mapping_status"] == "not_higher_education_establishment"

    if (concordance.loc[mapped, "dgeec_institution_code"] == "").any():
        raise ValueError("Mapped higher-education participants require a DGEEC code")
    if (concordance.loc[mapped, "dgeec_institution_name"] == "").any():
        raise ValueError("Mapped higher-education participants require a DGEEC name")
    if (concordance.loc[non_he, "dgeec_institution_code"] != "").any():
        raise ValueError("Non-higher-education participants must not carry a DGEEC code")
    if (concordance.loc[non_he, "dgeec_institution_name"] != "").any():
        raise ValueError("Non-higher-education participants must not carry a DGEEC name")


def build_weights(
    contract_path: Path,
    participation_path: Path,
    concordance_path: Path,
    expected_path: Path,
    panel_crosswalk_path: Path = DEFAULT_PANEL_CROSSWALK,
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
    unit_fields = _load_unit_fields(expected_path, panel_crosswalk_path)

    for column in ["unit_reference", "participant_institution_id", "participant_institution_name"]:
        participation[column] = participation[column].map(_normalise)
    for column in contract["concordance_required_columns"]:
        concordance[column] = concordance[column].map(_normalise)

    if participation.duplicated(["unit_reference", "participant_institution_id"]).any():
        raise ValueError("Participation input contains duplicate unit-participant rows")
    if concordance["participant_institution_id"].duplicated().any():
        raise ValueError("Concordance must classify each participant_institution_id exactly once")

    _validate_mapping_statuses(concordance, contract)

    concordance = concordance.rename(
        columns={
            "participant_institution_name": "participant_institution_name_concordance",
            "source_reference": "source_reference_concordance",
        }
    )
    joined = participation.merge(
        concordance,
        on="participant_institution_id",
        how="left",
        validate="many_to_one",
    )
    if joined["mapping_status"].fillna("").eq("").any():
        missing_ids = sorted(
            joined.loc[
                joined["mapping_status"].fillna("").eq(""),
                "participant_institution_id",
            ].unique()
        )
        raise ValueError(f"Missing participant concordance classification: {missing_ids[:10]}")

    joined = joined.merge(
        unit_fields,
        on="unit_reference",
        how="left",
        validate="many_to_one",
    )
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
                    "participant_institution_name": row["participant_institution_name"],
                    "concordance_participant_institution_name": row[
                        "participant_institution_name_concordance"
                    ],
                    "mapping_status": row["mapping_status"],
                    "dgeec_institution_code": row["dgeec_institution_code"],
                    "isced_f_scope": row["isced_f_scope"],
                    "weight": weight,
                    "weight_basis": basis,
                    "source_reference": row["source_reference"],
                }
            )

    output = pd.DataFrame(output_rows)
    tolerance = float(contract["rules"]["tolerance"])
    sums = output.groupby("unit_reference")["weight"].sum()
    bad = sums[(sums - 1.0).abs() > tolerance]
    if not bad.empty:
        raise ValueError(f"Unit weights do not sum to one: {bad.to_dict()}")
    return output.sort_values(
        ["unit_reference", "participant_institution_id"]
    ).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--participation", type=Path, default=DEFAULT_PARTICIPATION)
    parser.add_argument("--concordance", type=Path, default=DEFAULT_CONCORDANCE)
    parser.add_argument("--expected-units", type=Path, default=DEFAULT_EXPECTED)
    parser.add_argument("--panel-crosswalk", type=Path, default=DEFAULT_PANEL_CROSSWALK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    try:
        output = build_weights(
            args.contract,
            args.participation,
            args.concordance,
            args.expected_units,
            args.panel_crosswalk,
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
