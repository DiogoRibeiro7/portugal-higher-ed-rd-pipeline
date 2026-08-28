from __future__ import annotations

import pandas as pd

from pt_he_pipeline.modelling import fit_ols_summary, leave_one_year_out_rmse


def _frame() -> pd.DataFrame:
    rows = []
    for year in (2022, 2023, 2024, 2025):
        for institution, effect in (("A", 0.0), ("B", 5.0)):
            for demand in (1.0, 2.0, 3.0):
                rows.append({
                    "year": year,
                    "institution": institution,
                    "course": "engineering",
                    "demand": demand,
                    "grade": 120.0 + 10.0 * demand + effect + 0.5 * (year - 2022),
                })
    return pd.DataFrame(rows)


def test_fit_ols_summary_has_high_fit_for_deterministic_relation() -> None:
    fit = fit_ols_summary(
        _frame(),
        outcome="grade",
        numeric=("demand",),
        categorical=("year", "institution"),
        name="demand",
    )
    assert fit.n_obs == 24
    assert fit.r_squared > 0.99


def test_leave_one_year_out_rmse_is_finite() -> None:
    rmse = leave_one_year_out_rmse(
        _frame(),
        outcome="grade",
        year_column="year",
        numeric=("demand",),
        categorical=("institution",),
    )
    assert 0.0 <= rmse < 3.0
