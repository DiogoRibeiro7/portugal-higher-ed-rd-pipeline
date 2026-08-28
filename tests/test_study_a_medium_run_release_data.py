from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pt_he_pipeline.study_a import (
    build_endpoint_comparison,
    build_stem_component_metrics,
    build_stem_summary,
    validate_study_a_area_panel,
)
from pt_he_pipeline.study_a_trends import build_medium_run_coverage, fit_medium_run_trends

ROOT = Path(__file__).resolve().parents[1]
AREA_PATH = ROOT / "data/curated/dges/first_phase_area_2017_2026_observed.csv"
NATIONAL_PATH = ROOT / "data/curated/dges/national_first_phase_2013_2026.csv"
MANIFEST_PATH = ROOT / "data/source_manifests/dges_study_a_medium_run.csv"
EXPECTED_YEARS = list(range(2017, 2027))
OBSERVED_YEARS = [2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026]


def _release_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the committed medium-run Study A release inputs."""

    return pd.read_csv(AREA_PATH), pd.read_csv(NATIONAL_PATH)


def test_medium_run_area_panel_reconciles_every_source_locked_year() -> None:
    area, national = _release_inputs()
    validate_study_a_area_panel(area, national)

    assert len(area) == 207
    assert area.groupby("year").size().to_dict() == {year: 23 for year in OBSERVED_YEARS}
    assert 2019 not in set(area["year"])


def test_medium_run_manifest_never_claims_a_2019_observation() -> None:
    area, _ = _release_inputs()
    manifest = pd.read_csv(MANIFEST_PATH).set_index("year")
    coverage = build_medium_run_coverage(area["year"].astype(int), EXPECTED_YEARS).set_index("year")

    assert manifest.loc[2019, "coverage_status"] == "archive_audited_no_broad_area_table"
    assert pd.isna(manifest.loc[2019, "source_document"])
    assert not bool(coverage.loc[2019, "observed"])
    assert manifest.loc[2017, "source_table"] == "Quadro XII"


def test_medium_run_endpoint_result_matches_registered_counts() -> None:
    area, national = _release_inputs()
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components)
    endpoints = build_endpoint_comparison(components, summary).set_index("stem_code")

    summary_by_year = summary.set_index("year")
    assert int(summary_by_year.loc[2017, "placements"]) == 13926
    assert int(summary_by_year.loc[2026, "placements"]) == 15181
    assert float(endpoints.loc["05", "placement_change"]) == pytest.approx(-0.0678721174)
    assert float(endpoints.loc["06", "placement_change"]) == pytest.approx(0.60)
    assert float(endpoints.loc["07", "placement_change"]) == pytest.approx(0.1100107643)
    assert float(endpoints.loc["STEM", "placement_change"]) == pytest.approx(0.0901192015)


def test_medium_run_gap_is_not_mislabelled_as_one_year_change() -> None:
    area, national = _release_inputs()
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components).set_index("year")

    assert pd.isna(summary.loc[2020, "placement_yoy_change"])
    assert not pd.isna(summary.loc[2021, "placement_yoy_change"])


def test_medium_run_frozen_trend_specs_are_estimable() -> None:
    area, national = _release_inputs()
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components)

    main = fit_medium_run_trends(
        components,
        summary,
        expected_years=EXPECTED_YEARS,
        specification="all_observed",
    ).set_index("series_code")
    sensitivity = fit_medium_run_trends(
        components,
        summary,
        expected_years=EXPECTED_YEARS,
        exclude_years=[2020, 2021],
        specification="exclude_pandemic_years",
    ).set_index("series_code")

    assert int(main.loc["STEM", "n_obs"]) == 9
    assert main.loc["STEM", "missing_source_years"] == "2019"
    assert int(sensitivity.loc["STEM", "n_obs"]) == 7
    assert sensitivity.loc["STEM", "excluded_years"] == "2020,2021"
