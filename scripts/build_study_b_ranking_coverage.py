"""Build deterministic Study B ranking coverage outputs.

This script reconstructs the registered five-programme stable panel from the
committed DGES source shards, applies the explicit parent-university concordance,
and joins only provider/year coverage cells that are verified in the historical
audit. Unresolved cells remain unresolved and are never recoded as non-coverage.
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from pt_he_pipeline.study_b_multi_course import add_metrics, build_stable_panel, reconcile_sources
from scripts.build_study_b_multi_course import (
    DEFAULT_CONFIG,
    DEFAULT_SOURCE,
    _load_config,
    _load_source,
    _policy,
    _registry,
)

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CONCORDANCE: Final[Path] = ROOT / "data" / "curated" / "dges" / "study_b_parent_university_concordance.csv"
PROVIDER_STATUS: Final[Path] = ROOT / "data" / "curated" / "rankings" / "study_b_provider_coverage_status.csv"
OUTPUT: Final[Path] = ROOT / "results" / "study_b" / "ranking_coverage.csv"


def _split_ids(value: object) -> set[str]:
    """Parse a pipe-separated identifier field into a clean set."""
    if pd.isna(value):
        return set()
    text = str(value).strip()
    return {item for item in text.split("|") if item} if text else set()


def build() -> pd.DataFrame:
    """Rebuild and return provider-specific parent and programme-row coverage."""
    config = _load_config(DEFAULT_CONFIG)
    programmes = _registry(config)
    policy = _policy(config)
    source = _load_source(DEFAULT_SOURCE)
    canonical, reconciliation = reconcile_sources(source, programmes=programmes, policy=policy)
    stable, _ = build_stable_panel(
        canonical,
        reconciliation,
        programmes=programmes,
        policy=policy,
    )
    stable = add_metrics(stable, policy=policy)

    concordance = pd.read_csv(CONCORDANCE, dtype={"institution_code": str})
    status = pd.read_csv(PROVIDER_STATUS)

    mapping = concordance.loc[
        concordance["ranking_eligible_parent"].astype(bool),
        ["institution_code", "parent_institution_id"],
    ].dropna()
    if mapping["institution_code"].duplicated().any():
        raise ValueError("parent concordance contains duplicate institution codes")

    panel = stable.merge(mapping, on="institution_code", how="left", validate="many_to_one")
    eligible = panel.loc[panel["parent_institution_id"].notna()].copy()

    rows: list[dict[str, object]] = []
    for record in status.itertuples(index=False):
        verified = _split_ids(record.verified_parent_ids)
        unresolved = _split_ids(record.unresolved_parent_ids)
        year_panel = eligible.loc[eligible["year"] == int(record.admission_year)].copy()
        eligible_parents = set(year_panel["parent_institution_id"].astype(str))

        verified_in_panel = verified & eligible_parents
        unresolved_in_panel = unresolved & eligible_parents
        verified_mask = year_panel["parent_institution_id"].astype(str).isin(verified_in_panel)
        unresolved_mask = year_panel["parent_institution_id"].astype(str).isin(unresolved_in_panel)

        rows.append(
            {
                "provider": str(record.provider),
                "admission_year": int(record.admission_year),
                "coverage_status": str(record.coverage_status),
                "eligible_parent_institutions": len(eligible_parents),
                "verified_ranked_parent_institutions": len(verified_in_panel),
                "unresolved_parent_institutions": len(unresolved_in_panel),
                "eligible_rows": len(year_panel),
                "verified_ranked_rows": int(verified_mask.sum()),
                "unresolved_rows": int(unresolved_mask.sum()),
                "verified_row_coverage": (
                    float(verified_mask.mean()) if len(year_panel) else float("nan")
                ),
            }
        )

    result = pd.DataFrame(rows).sort_values(["provider", "admission_year"]).reset_index(drop=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)
    return result


def main() -> None:
    """CLI entry point."""
    print(build().to_string(index=False))


if __name__ == "__main__":
    main()
