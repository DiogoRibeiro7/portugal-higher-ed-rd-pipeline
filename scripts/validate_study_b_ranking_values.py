"""Validate the non-redistributed historical ranking panel for Study B."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Final

import pandas as pd

from pt_he_pipeline.study_b_rankings import validate_ranking_rows

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CONTRACT: Final[Path] = ROOT / "data" / "source_manifests" / "study_b_ranking_value_contract.json"


def _canonical_bytes(frame: pd.DataFrame, contract: dict[str, object]) -> bytes:
    """Return canonical CSV bytes used by the preregistered SHA-256 contract."""
    canonicalisation = contract["canonicalisation"]
    if not isinstance(canonicalisation, dict):
        raise TypeError("canonicalisation contract must be a mapping")
    columns = canonicalisation["column_order"]
    sort_columns = canonicalisation["sort_columns"]
    if not isinstance(columns, list) or not isinstance(sort_columns, list):
        raise TypeError("canonical column and sort specifications must be lists")
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"private ranking panel is missing columns: {sorted(missing)}")
    ordered = frame.loc[:, columns].sort_values(sort_columns).reset_index(drop=True)
    return ordered.to_csv(index=False, lineterminator="\n").encode("utf-8")


def validate_private_panel(path: Path | None = None) -> pd.DataFrame:
    """Validate timing, representation, membership counts and canonical panel hash."""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    panel_path = path or ROOT / str(contract["private_panel_path"])
    if not panel_path.exists():
        raise FileNotFoundError(
            f"authorised ranking panel not found at {panel_path}; "
            "provider values are intentionally not committed"
        )

    frame = pd.read_csv(panel_path, dtype={"parent_institution_id": str})
    validated = validate_ranking_rows(frame)

    if len(validated) != int(contract["expected_rows"]):
        raise ValueError("private ranking panel row count does not match frozen contract")

    expected = contract["expected_provider_year_counts"]
    if not isinstance(expected, dict):
        raise TypeError("expected_provider_year_counts must be a mapping")
    observed = validated.groupby(["provider", "admission_year"]).size()
    for provider, years in expected.items():
        if not isinstance(years, dict):
            raise TypeError("provider-year count contract must be a mapping")
        for year, count in years.items():
            actual = int(observed.get((provider, int(year)), 0))
            if actual != int(count):
                raise ValueError(
                    f"ranking membership mismatch for {provider} {year}: {actual} != {count}"
                )

    digest = hashlib.sha256(_canonical_bytes(frame, contract)).hexdigest()
    if digest != str(contract["canonical_sha256"]):
        raise ValueError("private ranking panel SHA-256 does not match frozen contract")
    return validated


def main() -> None:
    """CLI entry point."""
    frame = validate_private_panel()
    print(f"validated {len(frame)} Study B ranking observations")


if __name__ == "__main__":
    main()
