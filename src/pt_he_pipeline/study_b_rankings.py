"""Ranking/reputation utilities for the registered Study B design."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd
import statsmodels.api as sm

from pt_he_pipeline.validation import require_columns

PRIMARY_OUTCOMES: Final[tuple[str, ...]] = (
    "last_placed_general_contingent_grade",
    "mean_application_grade_placed",
)


@dataclass(frozen=True)
class RankingPolicy:
    """Validation policy for provider-specific ranking panels."""

    providers: tuple[str, ...] = ("QS", "Times Higher Education", "ARWU")
    first_year: int = 2018
    last_year: int = 2020

    @property
    def years(self) -> tuple[int, ...]:
        """Return the registered admission years."""

        return tuple(range(self.first_year, self.last_year + 1))


def validate_ranking_rows(
    rankings: pd.DataFrame,
    *,
    policy: RankingPolicy = RankingPolicy(),
) -> pd.DataFrame:
    """Validate provider-specific ranking observations without imputing coverage."""

    require_columns(
        rankings,
        (
            "admission_year",
            "provider",
            "parent_institution_id",
            "publication_date",
            "application_deadline",
            "rank",
            "rank_band",
        ),
    )
    frame = rankings.copy()
    frame["admission_year"] = pd.to_numeric(frame["admission_year"], errors="raise").astype(int)
    if not set(frame["admission_year"]).issubset(policy.years):
        raise ValueError("ranking rows contain years outside the registered window")
    if not set(frame["provider"]).issubset(policy.providers):
        raise ValueError("ranking rows contain an unregistered provider")
    frame["publication_date"] = pd.to_datetime(frame["publication_date"], errors="raise")
    frame["application_deadline"] = pd.to_datetime(frame["application_deadline"], errors="raise")
    if (frame["publication_date"] > frame["application_deadline"]).any():
        raise ValueError("ranking publication occurs after the application deadline")
    if frame.duplicated(["admission_year", "provider", "parent_institution_id"]).any():
        raise ValueError("duplicate provider/year/parent ranking observation")
    has_rank = pd.to_numeric(frame["rank"], errors="coerce").notna()
    has_band = frame["rank_band"].notna() & frame["rank_band"].astype(str).str.strip().ne("")
    if (has_rank & has_band).any():
        raise ValueError("ranking row must use exact rank or rank band, not both")
    return frame


def build_ranking_coverage(
    panel: pd.DataFrame,
    rankings: pd.DataFrame,
    *,
    provider: str,
) -> pd.DataFrame:
    """Report parent-institution and row coverage for one provider."""

    require_columns(panel, ("year", "parent_institution_id"))
    frame = validate_ranking_rows(rankings)
    ranked = frame.loc[frame["provider"] == provider, ["admission_year", "parent_institution_id"]]
    rows: list[dict[str, object]] = []
    for year, subset in panel.groupby("year", sort=True):
        eligible_parents = subset["parent_institution_id"].dropna().astype(str).nunique()
        keys = set(
            zip(
                ranked.loc[ranked["admission_year"] == year, "parent_institution_id"].astype(str),
                strict=False,
            )
        )
        ranked_mask = subset["parent_institution_id"].astype(str).map(lambda value: (value,) in keys)
        rows.append(
            {
                "year": int(year),
                "provider": provider,
                "eligible_parent_institutions": int(eligible_parents),
                "ranked_parent_institutions": int(
                    subset.loc[ranked_mask, "parent_institution_id"].astype(str).nunique()
                ),
                "eligible_rows": int(subset["parent_institution_id"].notna().sum()),
                "ranked_rows": int(ranked_mask.sum()),
            }
        )
    return pd.DataFrame(rows)


def leave_one_parent_out_rmse(
    frame: pd.DataFrame,
    *,
    outcome: str,
    include_demand: bool,
    include_ranking: bool,
) -> float:
    """Return LOPO RMSE for a complete provider-specific modelling frame."""

    require_columns(
        frame,
        (
            "programme_code",
            "year",
            "parent_institution_id",
            "applicants_per_vacancy",
            "ranking_score",
            outcome,
        ),
    )
    data = frame.dropna(
        subset=["programme_code", "year", "parent_institution_id", outcome]
    ).copy()
    if include_demand:
        data = data.loc[data["applicants_per_vacancy"] > 0].copy()
    if include_ranking:
        data = data.dropna(subset=["ranking_score"])
    predictions: list[float] = []
    observed: list[float] = []
    parents = sorted(data["parent_institution_id"].astype(str).unique())
    for parent in parents:
        test = data.loc[data["parent_institution_id"].astype(str) == parent]
        train = data.loc[data["parent_institution_id"].astype(str) != parent]
        if test.empty or train.empty:
            continue
        train_design = _design(train, include_demand=include_demand, include_ranking=include_ranking)
        test_design = _design(
            test,
            include_demand=include_demand,
            include_ranking=include_ranking,
            columns=list(train_design.columns),
        )
        model = sm.OLS(train[outcome].astype(float), train_design).fit()
        predictions.extend(model.predict(test_design).tolist())
        observed.extend(test[outcome].astype(float).tolist())
    if not observed:
        raise ValueError("leave-one-parent-out validation produced no test observations")
    residual = np.asarray(observed) - np.asarray(predictions)
    return float(np.sqrt(np.mean(residual**2)))


def _design(
    frame: pd.DataFrame,
    *,
    include_demand: bool,
    include_ranking: bool,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    data = pd.DataFrame(index=frame.index)
    categorical = pd.get_dummies(
        frame[["programme_code", "year"]].astype(str),
        prefix=["programme", "year"],
        drop_first=True,
        dtype=float,
    )
    data = pd.concat([data, categorical], axis=1)
    if include_demand:
        data["log_applicants_per_vacancy"] = np.log(frame["applicants_per_vacancy"].astype(float))
    if include_ranking:
        data["ranking_score"] = frame["ranking_score"].astype(float)
    data = sm.add_constant(data, has_constant="add")
    if columns is not None:
        data = data.reindex(columns=columns, fill_value=0.0)
    return data.astype(float)
