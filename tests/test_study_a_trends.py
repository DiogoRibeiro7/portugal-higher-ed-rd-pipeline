from __future__ import annotations

import math

import pandas as pd
import pytest

from pt_he_pipeline.study_a_trends import build_medium_run_coverage, fit_medium_run_trends


def _trend_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    years = [2017, 2018, 2020, 2021]
    component_rows: list[dict[str, float | int | str]] = []
    for code in ("05", "06", "07"):
        for year in years:
            elapsed = year - 2017
            component_rows.append(
                {
                    "year": year,
                    "stem_code": code,
                    "placements": 100.0 * math.exp(0.1 * elapsed),
                    "placement_share": 0.20 + 0.01 * elapsed,
                    "occupancy_rate": 0.70 + 0.02 * elapsed,
                    "first_choice_pressure": 0.80 - 0.01 * elapsed,
                }
            )

    summary_rows = []
    for year in years:
        elapsed = year - 2017
        summary_rows.append(
            {
                "year": year,
                "placements": 300.0 * math.exp(0.1 * elapsed),
                "placement_share": 0.60 + 0.01 * elapsed,
                "occupancy_rate": 0.75 + 0.02 * elapsed,
                "first_choice_pressure": 0.90 - 0.01 * elapsed,
            }
        )
    return pd.DataFrame(component_rows), pd.DataFrame(summary_rows)


def test_build_medium_run_coverage_preserves_source_gap() -> None:
    result = build_medium_run_coverage(
        [2017, 2018, 2020, 2021],
        [2017, 2018, 2019, 2020, 2021],
    ).set_index("year")

    assert bool(result.loc[2017, "observed"])
    assert not bool(result.loc[2019, "observed"])
    assert result.loc[2019, "status"] == "not_source_locked"


def test_fit_medium_run_trends_uses_calendar_year_spacing() -> None:
    components, summary = _trend_inputs()
    result = fit_medium_run_trends(
        components,
        summary,
        expected_years=[2017, 2018, 2019, 2020, 2021],
    ).set_index("series_code")

    assert float(result.loc["STEM", "placement_log_slope"]) == pytest.approx(0.1)
    assert float(result.loc["STEM", "placement_annual_trend_percent"]) == pytest.approx(
        100.0 * math.expm1(0.1)
    )
    assert float(result.loc["STEM", "placement_share_slope_pp_per_year"]) == pytest.approx(1.0)
    assert result.loc["STEM", "missing_source_years"] == "2019"


def test_fit_medium_run_trends_records_frozen_exclusion() -> None:
    components, summary = _trend_inputs()
    result = fit_medium_run_trends(
        components,
        summary,
        expected_years=[2017, 2018, 2019, 2020, 2021],
        exclude_years=[2020],
        specification="sensitivity",
    ).set_index("series_code")

    assert result.loc["STEM", "specification"] == "sensitivity"
    assert result.loc["STEM", "excluded_years"] == "2020"
    assert result.loc["STEM", "missing_source_years"] == "2019"
    assert int(result.loc["STEM", "n_obs"]) == 3


def test_fit_medium_run_trends_rejects_exclusion_outside_window() -> None:
    components, summary = _trend_inputs()
    with pytest.raises(ValueError, match="excluded years"):
        fit_medium_run_trends(
            components,
            summary,
            expected_years=[2017, 2018, 2019, 2020, 2021],
            exclude_years=[2016],
        )
