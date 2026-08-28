"""Matched-course demand/selectivity pilot for Study B.

The pilot holds the programme fixed at DGES course code 9119 (Engenharia
Informática, Licenciatura) and follows the same 23 institutions in 2018-2020.
Two consecutive DGES comparative course tables overlap in 2019.  The overlap is
used as a hard reconciliation check before a 69-row canonical panel is built.

All model summaries are descriptive.  The data are complete administrative
records for the matched course/institution set rather than a probability sample.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd
import statsmodels.api as sm

from pt_he_pipeline.validation import require_columns

IDENTIFIER_COLUMNS: Final[tuple[str, ...]] = (
    "year",
    "programme_code",
    "institution_code",
)

MEASURE_COLUMNS: Final[tuple[str, ...]] = (
    "vacancies",
    "applicants",
    "first_choice_applicants",
    "placements",
    "first_choice_placements",
    "last_placed_general_contingent_grade",
    "mean_application_grade_placed",
    "mean_entrance_exam_grade_placed",
    "mean_secondary_grade_placed",
)

SOURCE_REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "source_document_year",
    "source_url",
    "source_pages",
    "source_section",
    "source_type",
    "provider_bytes_bundled",
    "year",
    "programme_code",
    "programme_name",
    "degree",
    "institution_code",
    "institution_name",
    *MEASURE_COLUMNS,
)

PRIMARY_OUTCOMES: Final[tuple[str, ...]] = (
    "last_placed_general_contingent_grade",
    "mean_application_grade_placed",
)


@dataclass(frozen=True)
class MatchedCoursePolicy:
    """Coverage and identity requirements for the matched-course pilot."""

    programme_code: str = "9119"
    first_year: int = 2018
    last_year: int = 2020
    expected_institutions: int = 23
    overlap_year: int = 2019

    @property
    def expected_years(self) -> tuple[int, ...]:
        """Return the consecutive years required by the pilot."""

        return tuple(range(self.first_year, self.last_year + 1))


def validate_source_rows(
    source_rows: pd.DataFrame,
    *,
    policy: MatchedCoursePolicy = MatchedCoursePolicy(),
) -> None:
    """Validate source rows before overlapping vintages are reconciled."""

    require_columns(source_rows, SOURCE_REQUIRED_COLUMNS)
    if source_rows.empty:
        raise ValueError("matched-course source rows must not be empty")

    frame = source_rows.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["source_document_year"] = pd.to_numeric(
        frame["source_document_year"], errors="raise"
    ).astype(int)
    frame["programme_code"] = frame["programme_code"].astype(str).str.strip()
    frame["institution_code"] = (
        frame["institution_code"].astype(str).str.strip().str.zfill(4)
    )

    if set(frame["programme_code"]) != {policy.programme_code}:
        raise ValueError("source rows contain an unexpected programme code")
    if set(frame["year"]) != set(policy.expected_years):
        raise ValueError("source rows do not cover the registered pilot years")

    for column in (
        "vacancies",
        "applicants",
        "first_choice_applicants",
        "placements",
        "first_choice_placements",
    ):
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or (values < 0).any():
            raise ValueError(f"{column} must contain non-negative numeric counts")
        if not np.equal(values, np.floor(values)).all():
            raise ValueError(f"{column} must contain integer counts")

    for column in (
        "last_placed_general_contingent_grade",
        "mean_application_grade_placed",
        "mean_entrance_exam_grade_placed",
        "mean_secondary_grade_placed",
    ):
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or ((values < 0) | (values > 200)).any():
            raise ValueError(f"{column} must lie on the DGES 0-200 grade scale")

    if (frame["first_choice_applicants"] > frame["applicants"]).any():
        raise ValueError("first-choice applicants cannot exceed total applicants")
    if (frame["first_choice_placements"] > frame["placements"]).any():
        raise ValueError("first-choice placements cannot exceed total placements")
    if (frame["vacancies"] <= 0).any():
        raise ValueError("vacancies must be strictly positive")

    unique_institutions = frame.groupby("year")["institution_code"].nunique()
    if not (unique_institutions == policy.expected_institutions).all():
        raise ValueError("each pilot year must contain the registered institutions")

    source_key = ["source_document_year", *IDENTIFIER_COLUMNS]
    if frame.duplicated(source_key).any():
        raise ValueError("source table contains duplicate source-document observations")

    overlap = frame.loc[frame["year"] == policy.overlap_year]
    overlap_counts = overlap.groupby("institution_code")["source_document_year"].nunique()
    if not (overlap_counts == 2).all():
        raise ValueError("the registered overlap year must appear in both source documents")


def reconcile_overlapping_sources(
    source_rows: pd.DataFrame,
    *,
    policy: MatchedCoursePolicy = MatchedCoursePolicy(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hard-reconcile duplicated 2019 records and return a canonical panel.

    The contemporary document is selected after equality has been established.
    No averaging or source preference is allowed when overlapping values disagree.
    """

    validate_source_rows(source_rows, policy=policy)
    frame = source_rows.copy()
    frame["institution_code"] = (
        frame["institution_code"].astype(str).str.strip().str.zfill(4)
    )
    frame["programme_code"] = frame["programme_code"].astype(str).str.strip()

    reconciliation_rows: list[dict[str, object]] = []
    for key, group in frame.groupby(list(IDENTIFIER_COLUMNS), sort=True):
        disagreement = [
            column
            for column in MEASURE_COLUMNS
            if group[column].nunique(dropna=False) != 1
        ]
        if disagreement:
            year, programme_code, institution_code = key
            columns = ", ".join(disagreement)
            raise ValueError(
                "overlapping DGES source rows disagree for "
                f"{year}/{programme_code}/{institution_code}: {columns}"
            )
        reconciliation_rows.append(
            {
                "year": int(key[0]),
                "programme_code": str(key[1]),
                "institution_code": str(key[2]),
                "source_document_count": int(group["source_document_year"].nunique()),
                "reconciled": True,
            }
        )

    canonical = (
        frame.sort_values(
            ["year", "institution_code", "source_document_year"], kind="stable"
        )
        .drop_duplicates(list(IDENTIFIER_COLUMNS), keep="last")
        .sort_values(["year", "institution_code"], kind="stable")
        .reset_index(drop=True)
    )
    expected_rows = len(policy.expected_years) * policy.expected_institutions
    if len(canonical) != expected_rows:
        raise ValueError("canonical matched-course panel has an unexpected row count")

    reconciliation = pd.DataFrame(reconciliation_rows).sort_values(
        ["year", "institution_code"], kind="stable"
    )
    return canonical, reconciliation.reset_index(drop=True)


def add_course_pilot_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    """Add registered demand, occupancy and time variables to the canonical panel."""

    require_columns(panel, (*IDENTIFIER_COLUMNS, *MEASURE_COLUMNS))
    frame = panel.copy()
    vacancies = pd.to_numeric(frame["vacancies"], errors="raise").astype(float)
    if (vacancies <= 0).any():
        raise ValueError("vacancies must be strictly positive")

    frame["applicants_per_vacancy"] = frame["applicants"].astype(float) / vacancies
    frame["first_choice_pressure"] = (
        frame["first_choice_applicants"].astype(float) / vacancies
    )
    frame["occupancy_rate"] = frame["placements"].astype(float) / vacancies
    frame["year_offset"] = frame["year"].astype(int) - 2019
    return frame


def build_year_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Summarise the matched institutions separately by admission year."""

    require_columns(
        panel,
        (
            "year",
            "institution_code",
            "applicants_per_vacancy",
            "first_choice_pressure",
            *PRIMARY_OUTCOMES,
        ),
    )
    summary = (
        panel.groupby("year", as_index=False)
        .agg(
            institutions=("institution_code", "nunique"),
            mean_applicants_per_vacancy=("applicants_per_vacancy", "mean"),
            median_applicants_per_vacancy=("applicants_per_vacancy", "median"),
            mean_first_choice_pressure=("first_choice_pressure", "mean"),
            mean_cutoff=("last_placed_general_contingent_grade", "mean"),
            mean_placed_grade=("mean_application_grade_placed", "mean"),
        )
        .sort_values("year", kind="stable")
        .reset_index(drop=True)
    )
    return summary


def build_cross_section_associations(panel: pd.DataFrame) -> pd.DataFrame:
    """Estimate year-specific one-predictor grade associations.

    Two demand definitions are fitted separately.  R-squared is descriptive and
    should not be interpreted as a causal or sampling-inference statistic.
    """

    require_columns(
        panel,
        (
            "year",
            "applicants_per_vacancy",
            "first_choice_pressure",
            *PRIMARY_OUTCOMES,
        ),
    )
    rows: list[dict[str, object]] = []
    for year, subset in panel.groupby("year", sort=True):
        for demand in ("applicants_per_vacancy", "first_choice_pressure"):
            if (subset[demand] <= 0).any():
                raise ValueError(f"{demand} must be positive before log transformation")
            x = pd.DataFrame({"log_demand": np.log(subset[demand].astype(float))})
            design = sm.add_constant(x, has_constant="add")
            for outcome in PRIMARY_OUTCOMES:
                model = sm.OLS(subset[outcome].astype(float), design).fit()
                rows.append(
                    {
                        "year": int(year),
                        "outcome": outcome,
                        "demand_variable": demand,
                        "n": int(len(subset)),
                        "log_demand_coefficient": float(model.params["log_demand"]),
                        "r_squared": float(model.rsquared),
                        "adjusted_r_squared": float(model.rsquared_adj),
                    }
                )
    return pd.DataFrame(rows)


def build_nested_model_summary(panel: pd.DataFrame) -> pd.DataFrame:
    """Compare year, demand and institution fixed-effect descriptions."""

    frame = _validated_model_frame(panel)
    rows: list[dict[str, object]] = []
    specifications = (
        ("year", False, False),
        ("year_plus_demand", False, True),
        ("institution_year", True, False),
        ("institution_year_plus_demand", True, True),
    )
    for outcome in PRIMARY_OUTCOMES:
        fitted: dict[str, float] = {}
        for name, institution_effects, include_demand in specifications:
            design = _design_matrix(
                frame,
                institution_effects=institution_effects,
                include_demand=include_demand,
                institution_levels=sorted(frame["institution_code"].unique()),
            )
            model = sm.OLS(frame[outcome].astype(float), design).fit()
            predictions = model.predict(design)
            r_squared = float(model.rsquared)
            fitted[name] = r_squared
            baseline = (
                "institution_year" if institution_effects else "year"
            )
            incremental_r_squared = (
                r_squared - fitted[baseline]
                if include_demand and baseline in fitted
                else np.nan
            )
            rows.append(
                {
                    "outcome": outcome,
                    "model": name,
                    "n": int(len(frame)),
                    "parameters": int(len(model.params)),
                    "r_squared": r_squared,
                    "adjusted_r_squared": float(model.rsquared_adj),
                    "incremental_r_squared_vs_structure": incremental_r_squared,
                    "rmse": _rmse(frame[outcome].to_numpy(dtype=float), predictions),
                    "mae": _mae(frame[outcome].to_numpy(dtype=float), predictions),
                    "log_demand_coefficient": float(
                        model.params.get("log_applicants_per_vacancy", np.nan)
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_leave_one_year_out(panel: pd.DataFrame) -> pd.DataFrame:
    """Evaluate registered models by holding out each complete year in turn."""

    frame = _validated_model_frame(panel)
    levels = sorted(frame["institution_code"].unique())
    specifications = (
        ("year", False, False),
        ("year_plus_demand", False, True),
        ("institution_year", True, False),
        ("institution_year_plus_demand", True, True),
    )
    rows: list[dict[str, object]] = []
    for outcome in PRIMARY_OUTCOMES:
        for held_out_year in sorted(frame["year"].unique()):
            train = frame.loc[frame["year"] != held_out_year]
            test = frame.loc[frame["year"] == held_out_year]
            for name, institution_effects, include_demand in specifications:
                train_design = _design_matrix(
                    train,
                    institution_effects=institution_effects,
                    include_demand=include_demand,
                    institution_levels=levels,
                )
                test_design = _design_matrix(
                    test,
                    institution_effects=institution_effects,
                    include_demand=include_demand,
                    institution_levels=levels,
                )
                model = sm.OLS(train[outcome].astype(float), train_design).fit()
                predictions = model.predict(test_design).to_numpy(dtype=float)
                observed = test[outcome].to_numpy(dtype=float)
                rows.append(
                    {
                        "outcome": outcome,
                        "held_out_year": int(held_out_year),
                        "model": name,
                        "n_train": int(len(train)),
                        "n_test": int(len(test)),
                        "rmse": _rmse(observed, predictions),
                        "mae": _mae(observed, predictions),
                    }
                )
    return pd.DataFrame(rows)


def summarise_leave_one_year_out(loyo: pd.DataFrame) -> pd.DataFrame:
    """Average LOYO error across the three held-out years."""

    require_columns(loyo, ("outcome", "model", "held_out_year", "rmse", "mae"))
    return (
        loyo.groupby(["outcome", "model"], as_index=False)
        .agg(
            held_out_years=("held_out_year", "nunique"),
            mean_rmse=("rmse", "mean"),
            mean_mae=("mae", "mean"),
        )
        .sort_values(["outcome", "model"], kind="stable")
        .reset_index(drop=True)
    )


def _validated_model_frame(panel: pd.DataFrame) -> pd.DataFrame:
    """Validate variables shared by all matched-course models."""

    require_columns(
        panel,
        (
            "year",
            "institution_code",
            "applicants_per_vacancy",
            *PRIMARY_OUTCOMES,
        ),
    )
    frame = panel.copy()
    if (frame["applicants_per_vacancy"] <= 0).any():
        raise ValueError("applicants_per_vacancy must be positive")
    if frame["institution_code"].isna().any():
        raise ValueError("institution_code must not be missing")
    return frame


def _design_matrix(
    frame: pd.DataFrame,
    *,
    institution_effects: bool,
    include_demand: bool,
    institution_levels: list[str],
) -> pd.DataFrame:
    """Build a stable design matrix for estimation and held-out prediction."""

    design = pd.DataFrame(index=frame.index)
    design["year_offset"] = frame["year"].astype(float) - 2019.0
    if include_demand:
        design["log_applicants_per_vacancy"] = np.log(
            frame["applicants_per_vacancy"].astype(float)
        )
    if institution_effects:
        categories = pd.Categorical(
            frame["institution_code"].astype(str), categories=institution_levels
        )
        dummies = pd.get_dummies(
            categories,
            prefix="institution",
            drop_first=True,
            dtype=float,
        )
        dummies.index = frame.index
        design = pd.concat([design, dummies], axis=1)
    return sm.add_constant(design, has_constant="add")


def _rmse(observed: np.ndarray, predicted: np.ndarray | pd.Series) -> float:
    """Return root-mean-square prediction error."""

    prediction_array = np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean(np.square(observed - prediction_array))))


def _mae(observed: np.ndarray, predicted: np.ndarray | pd.Series) -> float:
    """Return mean absolute prediction error."""

    prediction_array = np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs(observed - prediction_array)))
