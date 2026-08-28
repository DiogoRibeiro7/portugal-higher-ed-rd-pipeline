from __future__ import annotations

import math

import pandas as pd
import pytest

from pt_he_pipeline.metrics import (
    add_access_metrics,
    compound_annual_growth,
    log_linear_trend,
    regionality_metrics,
    safe_ratio,
)


def test_safe_ratio_preserves_undefined_denominator() -> None:
    assert math.isnan(safe_ratio(10.0, 0.0))
    assert safe_ratio(10.0, 4.0) == pytest.approx(2.5)


def test_add_access_metrics() -> None:
    frame = pd.DataFrame({
        "applicants": [100, 5],
        "vacancies": [20, 0],
        "placements": [20, 0],
        "first_choice_applicants": [30, 1],
    })
    result = add_access_metrics(frame)
    assert result.loc[0, "applicants_per_vacancy"] == pytest.approx(5.0)
    assert result.loc[0, "occupancy_rate"] == pytest.approx(1.0)
    assert result.loc[0, "first_choice_pressure"] == pytest.approx(1.5)
    assert math.isnan(float(result.loc[1, "applicants_per_vacancy"]))


def test_regionality_metrics_identify_diagonal_concentration() -> None:
    matrix = pd.DataFrame(
        [[80, 20], [10, 90]],
        index=["North", "South"],
        columns=["North", "South"],
    )
    result = regionality_metrics(matrix)
    assert result.total_flow == pytest.approx(200.0)
    assert result.same_district_share == pytest.approx(0.85)
    assert 0.0 <= result.normalised_entropy <= 1.0
    assert result.mutual_information > 0.0


def test_log_linear_trend_recovers_constant_growth() -> None:
    years = pd.Series([2020, 2021, 2022, 2023])
    values = pd.Series([100.0, 110.0, 121.0, 133.1])
    result = log_linear_trend(years, values)
    assert result.approximate_annual_percent_change == pytest.approx(10.0, abs=1e-8)
    assert result.r_squared == pytest.approx(1.0)


def test_compound_annual_growth() -> None:
    assert compound_annual_growth(100.0, 121.0, 2) == pytest.approx(0.1)
