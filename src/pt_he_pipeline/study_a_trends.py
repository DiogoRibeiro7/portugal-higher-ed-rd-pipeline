"""Descriptive medium-run trend helpers for Study A.

The release intentionally treats the broad-area series as administrative counts,
not as a probability sample.  The fitted lines are descriptive summaries of the
observed annual path.  They are not causal models and are not used to manufacture
values for source years that have not been locked.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from pt_he_pipeline.study_a import STEM_COMPONENT_LABELS
from pt_he_pipeline.validation import require_columns

_TREND_REQUIRED_COLUMNS = (
    "year",
    "placements",
    "placement_share",
    "occupancy_rate",
    "first_choice_pressure",
)


@dataclass(frozen=True)
class LinearFit:
    """Minimal deterministic ordinary-least-squares summary."""

    intercept: float
    slope: float
    r_squared: float
    n_obs: int


def _fit_linear(x: np.ndarray, y: np.ndarray) -> LinearFit:
    """Fit ``y = intercept + slope * x`` and return an effect-size summary."""

    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("x and y must be one-dimensional")
    if x.size != y.size:
        raise ValueError("x and y must contain the same number of observations")
    if x.size < 3:
        raise ValueError("a descriptive trend requires at least three observations")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("trend inputs must be finite")
    if np.unique(x).size != x.size:
        raise ValueError("trend years must be unique")

    centred_x = x - float(np.mean(x))
    design = np.column_stack((np.ones_like(centred_x), centred_x))
    coefficients, _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if int(rank) != 2:
        raise ValueError("trend design is rank deficient")

    fitted = design @ coefficients
    residual_sum_squares = float(np.sum((y - fitted) ** 2))
    total_sum_squares = float(np.sum((y - float(np.mean(y))) ** 2))
    if total_sum_squares == 0.0:
        r_squared = 1.0 if residual_sum_squares == 0.0 else 0.0
    else:
        r_squared = 1.0 - residual_sum_squares / total_sum_squares

    # Convert the centred intercept back to the original year scale so that the
    # returned coefficients describe the usual y = a + b * year equation.
    slope = float(coefficients[1])
    intercept = float(coefficients[0]) - slope * float(np.mean(x))
    return LinearFit(
        intercept=intercept,
        slope=slope,
        r_squared=r_squared,
        n_obs=int(x.size),
    )


def _normalise_years(values: Iterable[int]) -> tuple[int, ...]:
    """Return sorted unique integer years with explicit validation."""

    years = tuple(sorted({int(value) for value in values}))
    if not years:
        raise ValueError("expected years must not be empty")
    return years


def build_medium_run_coverage(
    observed_years: Iterable[int],
    expected_years: Iterable[int],
) -> pd.DataFrame:
    """Return one row per expected year with an explicit source-coverage flag."""

    observed = set(_normalise_years(observed_years))
    expected = _normalise_years(expected_years)
    unexpected = sorted(observed.difference(expected))
    if unexpected:
        raise ValueError(f"observed years fall outside the expected window: {unexpected}")

    return pd.DataFrame(
        {
            "year": list(expected),
            "observed": [year in observed for year in expected],
            "status": [
                "source_locked" if year in observed else "not_source_locked"
                for year in expected
            ],
        }
    )


def _fit_series(
    frame: pd.DataFrame,
    *,
    series_code: str,
    series_label: str,
    expected_years: Sequence[int],
    excluded_years: Sequence[int],
    specification: str,
) -> dict[str, float | int | str]:
    """Fit the registered descriptive metrics for one component or all-STEM series."""

    require_columns(frame, _TREND_REQUIRED_COLUMNS)
    data = frame.copy()
    data["year"] = pd.to_numeric(data["year"], errors="raise").astype(int)
    data = data.loc[~data["year"].isin(set(excluded_years))].sort_values("year", kind="stable")
    if data.empty:
        raise ValueError(f"no observations remain for {series_code}")
    if data["year"].duplicated().any():
        raise ValueError(f"duplicate years in trend series {series_code}")

    years = data["year"].to_numpy(dtype=float)
    placement_values = pd.to_numeric(data["placements"], errors="raise").to_numpy(dtype=float)
    if (placement_values <= 0.0).any():
        raise ValueError("placement counts must be strictly positive for log trends")

    log_placements = _fit_linear(years, np.log(placement_values))
    placement_share = _fit_linear(
        years,
        pd.to_numeric(data["placement_share"], errors="raise").to_numpy(dtype=float),
    )
    occupancy = _fit_linear(
        years,
        pd.to_numeric(data["occupancy_rate"], errors="raise").to_numpy(dtype=float),
    )
    first_choice_pressure = _fit_linear(
        years,
        pd.to_numeric(data["first_choice_pressure"], errors="raise").to_numpy(dtype=float),
    )

    observed = set(data["year"].astype(int).tolist())
    expected_after_exclusion = [year for year in expected_years if year not in set(excluded_years)]
    missing = [year for year in expected_after_exclusion if year not in observed]

    return {
        "specification": specification,
        "series_code": series_code,
        "series_label": series_label,
        "n_obs": log_placements.n_obs,
        "first_year": int(data["year"].min()),
        "last_year": int(data["year"].max()),
        "excluded_years": ",".join(str(year) for year in excluded_years),
        "missing_source_years": ",".join(str(year) for year in missing),
        "placement_log_slope": log_placements.slope,
        "placement_annual_trend_percent": 100.0 * float(np.expm1(log_placements.slope)),
        "placement_r_squared": log_placements.r_squared,
        "placement_share_slope_pp_per_year": 100.0 * placement_share.slope,
        "placement_share_r_squared": placement_share.r_squared,
        "occupancy_slope_pp_per_year": 100.0 * occupancy.slope,
        "occupancy_r_squared": occupancy.r_squared,
        "first_choice_pressure_slope_pp_per_year": 100.0 * first_choice_pressure.slope,
        "first_choice_pressure_r_squared": first_choice_pressure.r_squared,
    }


def fit_medium_run_trends(
    component_metrics: pd.DataFrame,
    stem_summary: pd.DataFrame,
    *,
    expected_years: Sequence[int],
    exclude_years: Sequence[int] = (),
    specification: str = "all_observed",
) -> pd.DataFrame:
    """Fit descriptive annual trends for each STEM component and the all-STEM aggregate.

    Missing source years remain missing.  The calendar year itself is the regressor,
    so a two-year source gap is represented by a two-unit spacing rather than being
    silently compressed into one pseudo-year.
    """

    require_columns(component_metrics, ("year", "stem_code", *_TREND_REQUIRED_COLUMNS[1:]))
    require_columns(stem_summary, _TREND_REQUIRED_COLUMNS)
    if component_metrics.empty or stem_summary.empty:
        raise ValueError("component metrics and STEM summary must not be empty")

    expected = _normalise_years(expected_years)
    excluded = tuple(sorted({int(year) for year in exclude_years}))
    if set(excluded).difference(expected):
        raise ValueError("excluded years must lie inside the expected window")

    rows: list[dict[str, float | int | str]] = []
    for code, label in STEM_COMPONENT_LABELS.items():
        subset = component_metrics.loc[component_metrics["stem_code"] == code].copy()
        rows.append(
            _fit_series(
                subset,
                series_code=code,
                series_label=label,
                expected_years=expected,
                excluded_years=excluded,
                specification=specification,
            )
        )

    rows.append(
        _fit_series(
            stem_summary,
            series_code="STEM",
            series_label="All registered STEM",
            expected_years=expected,
            excluded_years=excluded,
            specification=specification,
        )
    )
    return pd.DataFrame(rows)
