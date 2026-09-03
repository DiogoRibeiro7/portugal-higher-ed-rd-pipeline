from __future__ import annotations

import math

import pandas as pd
import pytest
from dataexcept import DataValidationError, MissingColumnError

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


def test_add_access_metrics_rejects_missing_column_with_dataexcept() -> None:
    with pytest.raises(MissingColumnError):
        add_access_metrics(pd.DataFrame({"applicants": [10], "vacancies": [5]}))


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


def test_regionality_metrics_aligns_diagonal_by_label_identity() -> None:
    matrix = pd.DataFrame(
        [[20, 80], [90, 10]],
        index=[1, "1"],
        columns=["1", 1],
    )
    result = regionality_metrics(matrix)
    assert result.total_flow == pytest.approx(200.0)
    assert result.same_district_share == pytest.approx(0.85)


def test_regionality_metrics_rejects_nonnumeric_flow_with_dataexcept() -> None:
    matrix = pd.DataFrame([[1, "bad"], [2, 3]], index=["A", "B"], columns=["A", "B"])
    with pytest.raises(DataValidationError, match="numeric"):
        regionality_metrics(matrix)


def test_log_linear_trend_recovers_constant_growth() -> None:
    years = pd.Series([2020, 2021, 2022, 2023])
    values = pd.Series([100.0, 110.0, 121.0, 133.1])
    result = log_linear_trend(years, values)
    assert result.approximate_annual_percent_change == pytest.approx(10.0, abs=1e-8)
    assert result.r_squared == pytest.approx(1.0)


def test_log_linear_trend_rejects_insufficient_data_with_dataexcept() -> None:
    years = pd.Series([2020, 2021])
    values = pd.Series([100.0, 110.0])
    with pytest.raises(DataValidationError, match="three positive observations"):
        log_linear_trend(years, values)


def test_compound_annual_growth() -> None:
    assert compound_annual_growth(100.0, 121.0, 2) == pytest.approx(0.1)


def test_compound_annual_growth_keeps_programmer_preconditions_as_value_error() -> None:
    with pytest.raises(ValueError, match="years must be positive"):
        compound_annual_growth(100.0, 121.0, 0)
