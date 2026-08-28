"""Small, explicit modelling utilities for nested explanatory comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass(frozen=True, slots=True)
class NestedFit:
    """Summary of one OLS model in a nested comparison."""

    name: str
    n_obs: int
    r_squared: float
    adjusted_r_squared: float
    rmse: float
    mae: float


def _design_matrix(
    frame: pd.DataFrame,
    numeric: Sequence[str],
    categorical: Sequence[str],
) -> pd.DataFrame:
    """Build a deterministic full-rank design matrix with reference categories."""

    parts: list[pd.DataFrame] = []
    if numeric:
        numeric_frame = frame.loc[:, list(numeric)].apply(pd.to_numeric, errors="coerce")
        parts.append(numeric_frame)
    if categorical:
        categorical_frame = pd.get_dummies(
            frame.loc[:, list(categorical)].astype("string"),
            drop_first=True,
            dtype=float,
        )
        parts.append(categorical_frame)
    if not parts:
        return pd.DataFrame(index=frame.index)
    return pd.concat(parts, axis=1)


def fit_ols_summary(
    frame: pd.DataFrame,
    *,
    outcome: str,
    numeric: Sequence[str] = (),
    categorical: Sequence[str] = (),
    name: str = "model",
) -> NestedFit:
    """Fit OLS and return transparent fit statistics.

    Rows with missing outcome or predictors are removed jointly. This function
    is intended for descriptive model comparison, not causal identification.
    """

    required = {outcome, *numeric, *categorical}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    design = _design_matrix(frame, numeric, categorical)
    response = pd.to_numeric(frame[outcome], errors="coerce").rename(outcome)
    combined = pd.concat([response, design], axis=1).dropna(axis=0, how="any")
    if combined.shape[0] < 3:
        raise ValueError("at least three complete observations are required")

    y = combined[outcome].astype(float)
    x = sm.add_constant(combined.drop(columns=[outcome]).astype(float), has_constant="add")
    fit = sm.OLS(y, x).fit()
    prediction = fit.predict(x)
    residual = y - prediction

    return NestedFit(
        name=name,
        n_obs=int(fit.nobs),
        r_squared=float(fit.rsquared),
        adjusted_r_squared=float(fit.rsquared_adj),
        rmse=float(np.sqrt(np.mean(np.square(residual)))),
        mae=float(np.mean(np.abs(residual))),
    )


def leave_one_year_out_rmse(
    frame: pd.DataFrame,
    *,
    outcome: str,
    year_column: str,
    numeric: Sequence[str] = (),
    categorical: Sequence[str] = (),
) -> float:
    """Compute leave-one-year-out RMSE for an OLS specification.

    Categorical levels unseen in the training fold are handled through a
    training-derived dummy schema; unseen levels therefore receive the
    reference-category contribution rather than causing a shape mismatch.
    """

    required = {outcome, year_column, *numeric, *categorical}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")

    squared_errors: list[float] = []
    years = sorted(frame[year_column].dropna().unique().tolist())
    if len(years) < 2:
        raise ValueError("at least two years are required")

    for held_out in years:
        train = frame.loc[frame[year_column] != held_out].copy()
        test = frame.loc[frame[year_column] == held_out].copy()

        train_x = _design_matrix(train, numeric, categorical)
        test_x = _design_matrix(test, numeric, categorical)
        test_x = test_x.reindex(columns=train_x.columns, fill_value=0.0)

        train_y = pd.to_numeric(train[outcome], errors="coerce").rename(outcome)
        test_y = pd.to_numeric(test[outcome], errors="coerce").rename(outcome)
        train_complete = pd.concat([train_y, train_x], axis=1).dropna()
        test_complete = pd.concat([test_y, test_x], axis=1).dropna()
        if train_complete.empty or test_complete.empty:
            continue

        x_train = sm.add_constant(
            train_complete.drop(columns=[outcome]).astype(float),
            has_constant="add",
        )
        fit = sm.OLS(train_complete[outcome].astype(float), x_train).fit()
        x_test = sm.add_constant(
            test_complete.drop(columns=[outcome]).astype(float),
            has_constant="add",
        )
        x_test = x_test.reindex(columns=x_train.columns, fill_value=0.0)
        predictions = fit.predict(x_test)
        errors = test_complete[outcome].astype(float).to_numpy() - predictions.to_numpy()
        squared_errors.extend(np.square(errors).tolist())

    if not squared_errors:
        raise ValueError("no complete validation folds were available")
    return float(np.sqrt(np.mean(squared_errors)))
