"""Core transparent metrics used by the three studies."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from pt_he_pipeline.types import RegionalityMetrics, TrendSummary


def safe_ratio(numerator: float, denominator: float) -> float:
    """Return a ratio, preserving undefined zero-denominator cases as NaN."""

    if not math.isfinite(numerator) or not math.isfinite(denominator):
        return math.nan
    if denominator == 0:
        return math.nan
    return numerator / denominator


def add_access_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Add demand and occupancy ratios to a CNA course–institution panel.

    Missing/zero denominators yield ``NaN`` rather than infinity or an invented
    zero. The input frame is not mutated.
    """

    required = {"applicants", "vacancies", "placements"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    output = frame.copy()
    vacancies = pd.to_numeric(output["vacancies"], errors="coerce")
    applicants = pd.to_numeric(output["applicants"], errors="coerce")
    placements = pd.to_numeric(output["placements"], errors="coerce")

    denominator = vacancies.where(vacancies != 0)
    output["applicants_per_vacancy"] = applicants / denominator
    output["occupancy_rate"] = placements / denominator

    if "first_choice_applicants" in output.columns:
        first_choice = pd.to_numeric(output["first_choice_applicants"], errors="coerce")
        output["first_choice_pressure"] = first_choice / denominator

    return output


def regionality_metrics(matrix: pd.DataFrame) -> RegionalityMetrics:
    """Compute summary statistics for a square origin-destination flow matrix.

    Rows are origins and columns are destinations. Labels are used to identify
    the diagonal, so row/column order need not match.
    """

    if matrix.empty:
        raise ValueError("matrix must not be empty")
    if set(matrix.index) != set(matrix.columns):
        raise ValueError("matrix must have matching origin and destination labels")

    values = matrix.astype(float)
    if values.isna().any().any():
        raise ValueError("matrix must not contain missing values")
    if (values.to_numpy() < 0).any():
        raise ValueError("flows must be non-negative")

    total = float(values.to_numpy().sum())
    if total <= 0:
        raise ValueError("matrix must contain positive total flow")

    diagonal = sum(float(values.loc[label, label]) for label in values.index)
    same_share = diagonal / total

    # Conditional destination entropy averaged over origins, normalised to [0, 1].
    n_destinations = values.shape[1]
    entropy_scale = math.log(n_destinations) if n_destinations > 1 else 1.0
    weighted_entropy = 0.0
    row_totals = values.sum(axis=1)
    for label, row_total in row_totals.items():
        if row_total <= 0:
            continue
        probabilities = (values.loc[label] / row_total).to_numpy(dtype=float)
        positive = probabilities[probabilities > 0]
        entropy = -float(np.sum(positive * np.log(positive))) / entropy_scale
        weighted_entropy += (float(row_total) / total) * entropy

    # Mutual information between origin and destination, in nats.
    joint = values.to_numpy(dtype=float) / total
    p_origin = joint.sum(axis=1, keepdims=True)
    p_destination = joint.sum(axis=0, keepdims=True)
    expected = p_origin @ p_destination
    positive_mask = joint > 0
    mutual_information = float(
        np.sum(joint[positive_mask] * np.log(joint[positive_mask] / expected[positive_mask]))
    )

    return RegionalityMetrics(
        total_flow=total,
        same_district_share=same_share,
        normalised_entropy=weighted_entropy,
        mutual_information=mutual_information,
    )


def log_linear_trend(years: pd.Series, values: pd.Series) -> TrendSummary:
    """Estimate a simple log-linear annual trend for positive observations."""

    x = pd.to_numeric(years, errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(values, errors="coerce").to_numpy(dtype=float)
    valid = np.isfinite(x) & np.isfinite(y) & (y > 0)
    x = x[valid]
    y = y[valid]
    if x.size < 3:
        raise ValueError("at least three positive observations are required")

    x_centered = x - x.mean()
    log_y = np.log(y)
    design = np.column_stack([np.ones(x.size), x_centered])
    beta, *_ = np.linalg.lstsq(design, log_y, rcond=None)
    fitted = design @ beta
    residual = log_y - fitted
    ss_res = float(residual @ residual)
    centred = log_y - log_y.mean()
    ss_tot = float(centred @ centred)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    slope = float(beta[1])
    annual_change = 100.0 * (math.exp(slope) - 1.0)
    return TrendSummary(
        n_years=int(x.size),
        slope_log_units_per_year=slope,
        approximate_annual_percent_change=annual_change,
        r_squared=r_squared,
    )


def compound_annual_growth(start: float, end: float, years: int) -> float:
    """Return compound annual growth as a decimal fraction."""

    if years <= 0:
        raise ValueError("years must be positive")
    if start <= 0 or end < 0:
        raise ValueError("start must be positive and end must be non-negative")
    if end == 0:
        return -1.0
    return (end / start) ** (1.0 / years) - 1.0
