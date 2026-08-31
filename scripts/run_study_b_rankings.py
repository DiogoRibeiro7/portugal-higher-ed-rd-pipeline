"""Run the registered Study B provider-specific ranking analysis.

The runner fails closed. It validates the non-redistributed private ranking panel
against the frozen SHA-256 contract, rebuilds the registered five-programme DGES
panel from committed source shards, applies the explicit parent-university
concordance, checks provider-specific row coverage, and then performs paired
leave-one-parent-institution-out comparisons on identical supported observations.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Final

import pandas as pd

from scripts.build_study_b_multi_course import (
    DEFAULT_CONFIG,
    DEFAULT_SOURCE,
    _load_config,
    _load_source,
    _policy,
    _registry,
)
from scripts.validate_study_b_ranking_values import validate_private_panel
from pt_he_pipeline.study_b_multi_course import add_metrics, build_stable_panel, reconcile_sources
from pt_he_pipeline.study_b_rankings import (
    PRIMARY_OUTCOMES,
    RankingPolicy,
    leave_one_parent_out_comparison,
)

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CONCORDANCE: Final[Path] = (
    ROOT / "data" / "curated" / "dges" / "study_b_parent_university_concordance.csv"
)
COVERAGE: Final[Path] = ROOT / "results" / "study_b" / "ranking_coverage.csv"
OUTPUT: Final[Path] = ROOT / "results" / "study_b" / "ranking_model_comparisons.csv"


def _stable_parent_panel() -> pd.DataFrame:
    """Rebuild the registered stable panel and attach explicit parent universities."""

    config = _load_config(DEFAULT_CONFIG)
    programmes = _registry(config)
    policy = _policy(config)
    source = _load_source(DEFAULT_SOURCE)
    canonical, reconciliation = reconcile_sources(
        source,
        programmes=programmes,
        policy=policy,
    )
    stable, _ = build_stable_panel(
        canonical,
        reconciliation,
        programmes=programmes,
        policy=policy,
    )
    stable = add_metrics(stable, policy=policy)

    concordance = pd.read_csv(CONCORDANCE, dtype={"institution_code": str})
    mapping = concordance.loc[
        concordance["ranking_eligible_parent"].astype(bool),
        ["institution_code", "parent_institution_id"],
    ].dropna()
    if mapping["institution_code"].duplicated().any():
        raise ValueError("parent concordance contains duplicate institution codes")

    panel = stable.merge(mapping, on="institution_code", how="left", validate="many_to_one")
    return panel.loc[panel["parent_institution_id"].notna()].copy()


def _join_provider_rankings(
    panel: pd.DataFrame,
    rankings: pd.DataFrame,
    *,
    provider: str,
) -> pd.DataFrame:
    """Join one provider's validated ranking observations onto the DGES panel."""

    provider_rankings = rankings.loc[rankings["provider"] == provider].copy()
    provider_rankings = provider_rankings.rename(columns={"admission_year": "year"})
    joined = panel.merge(
        provider_rankings[
            [
                "year",
                "parent_institution_id",
                "provider",
                "rank",
                "rank_band",
                "publication_date",
                "application_deadline",
            ]
        ],
        on=["year", "parent_institution_id"],
        how="left",
        validate="many_to_one",
    )
    return joined


def _assert_frozen_row_coverage(joined: pd.DataFrame, *, provider: str) -> None:
    """Require the joined ranking rows to match the committed coverage gate."""

    coverage = pd.read_csv(COVERAGE)
    expected = coverage.loc[coverage["provider"] == provider].set_index("admission_year")
    if expected.empty:
        raise ValueError(f"missing committed ranking coverage for {provider}")

    has_ranking = pd.to_numeric(joined["rank"], errors="coerce").notna() | (
        joined["rank_band"].fillna("").astype(str).str.strip().ne("")
    )
    observed = joined.loc[has_ranking].groupby("year").size()
    for year, row in expected.iterrows():
        actual = int(observed.get(int(year), 0))
        required = int(row["verified_ranked_rows"])
        if actual != required:
            raise ValueError(
                f"joined ranking row coverage mismatch for {provider} {year}: "
                f"{actual} != {required}"
            )


def _result_row(
    *,
    provider: str,
    comparison: str,
    outcome: str,
    include_demand: bool,
    frame: pd.DataFrame,
) -> dict[str, object]:
    """Run one paired LOPO comparison and return a flat release row."""

    result = leave_one_parent_out_comparison(
        frame,
        outcome=outcome,
        include_demand=include_demand,
    )
    payload: dict[str, object] = {
        "provider": provider,
        "comparison": comparison,
        "outcome": outcome,
        "include_demand": include_demand,
    }
    payload.update(asdict(result))
    payload["delta_rmse"] = result.delta_rmse
    payload["delta_mae"] = result.delta_mae
    return payload


def analyse_provider(frame: pd.DataFrame, *, provider: str) -> pd.DataFrame:
    """Return the five registered predictive comparisons for one provider."""

    rows: list[dict[str, object]] = []
    for outcome in PRIMARY_OUTCOMES:
        rows.append(
            _result_row(
                provider=provider,
                comparison="M0_vs_MR",
                outcome=outcome,
                include_demand=False,
                frame=frame,
            )
        )
        rows.append(
            _result_row(
                provider=provider,
                comparison="MD_vs_MDR",
                outcome=outcome,
                include_demand=True,
                frame=frame,
            )
        )

    rows.append(
        _result_row(
            provider=provider,
            comparison="M0_vs_MR_demand",
            outcome="applicants_per_vacancy",
            include_demand=False,
            frame=frame,
        )
    )
    return pd.DataFrame(rows)


def run(*, ranking_path: Path | None = None) -> pd.DataFrame:
    """Validate inputs, run all provider comparisons, and write release output."""

    rankings = validate_private_panel(ranking_path)
    panel = _stable_parent_panel()

    frames: list[pd.DataFrame] = []
    for provider in RankingPolicy().providers:
        joined = _join_provider_rankings(panel, rankings, provider=provider)
        _assert_frozen_row_coverage(joined, provider=provider)
        frames.append(analyse_provider(joined, provider=provider))

    result = pd.concat(frames, ignore_index=True)
    result = result.sort_values(["provider", "comparison", "outcome"]).reset_index(drop=True)
    if len(result) != 15:
        raise ValueError(f"registered ranking analysis must produce 15 comparison rows, got {len(result)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)
    return result


def main() -> None:
    """CLI entry point."""

    result = run()
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
