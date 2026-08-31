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


@dataclass(frozen=True)
class LopoComparisonResult:
    """Paired LOPO metrics on identical supported observations."""

    baseline_rmse: float
    ranking_rmse: float
    baseline_mae: float
    ranking_mae: float
    eligible_rows: int
    eligible_parents: int
    supported_rows: int
    unsupported_rows: int
    supported_parents: int
    unsupported_ranking_rows: int = 0
    unsupported_structural_rows: int = 0

    @property
    def delta_rmse(self) -> float:
        """Return ranking-model RMSE minus baseline RMSE."""

        return self.ranking_rmse - self.baseline_rmse

    @property
    def delta_mae(self) -> float:
        """Return ranking-model MAE minus baseline MAE."""

        return self.ranking_mae - self.baseline_mae


@dataclass(frozen=True)
class DesignSchema:
    """Training-owned categorical levels and references for one LOPO fold."""

    programme_levels: tuple[str, ...]
    year_levels: tuple[str, ...]
    ranking_band_levels: tuple[str, ...] = ()


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
    frame["admission_year"] = pd.to_numeric(
        frame["admission_year"], errors="raise"
    ).astype(int)
    if not set(frame["admission_year"]).issubset(policy.years):
        raise ValueError("ranking rows contain years outside the registered window")
    if not set(frame["provider"]).issubset(policy.providers):
        raise ValueError("ranking rows contain an unregistered provider")
    frame["publication_date"] = pd.to_datetime(
        frame["publication_date"], errors="raise"
    )
    frame["application_deadline"] = pd.to_datetime(
        frame["application_deadline"], errors="raise"
    )
    if (frame["publication_date"] > frame["application_deadline"]).any():
        raise ValueError("ranking publication occurs after the application deadline")
    if frame.duplicated(
        ["admission_year", "provider", "parent_institution_id"]
    ).any():
        raise ValueError("duplicate provider/year/parent ranking observation")

    numeric_rank = pd.to_numeric(frame["rank"], errors="coerce")
    has_rank = numeric_rank.notna()
    has_band = (
        frame["rank_band"].notna()
        & frame["rank_band"].astype(str).str.strip().ne("")
    )
    if (has_rank & has_band).any():
        raise ValueError("ranking row must use exact rank or rank band, not both")
    if (numeric_rank.loc[has_rank] <= 0).any():
        raise ValueError("exact ranks must be strictly positive")
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
    ranked = frame.loc[
        frame["provider"] == provider,
        ["admission_year", "parent_institution_id"],
    ]
    rows: list[dict[str, object]] = []
    for year, subset in panel.groupby("year", sort=True):
        eligible_parents = (
            subset["parent_institution_id"].dropna().astype(str).nunique()
        )
        keys = set(
            zip(
                ranked.loc[
                    ranked["admission_year"] == year,
                    "parent_institution_id",
                ].astype(str),
                strict=False,
            )
        )
        ranked_mask = subset["parent_institution_id"].astype(str).map(
            lambda value: (value,) in keys
        )
        rows.append(
            {
                "year": int(year),
                "provider": provider,
                "eligible_parent_institutions": int(eligible_parents),
                "ranked_parent_institutions": int(
                    subset.loc[ranked_mask, "parent_institution_id"]
                    .astype(str)
                    .nunique()
                ),
                "eligible_rows": int(
                    subset["parent_institution_id"].notna().sum()
                ),
                "ranked_rows": int(ranked_mask.sum()),
            }
        )
    return pd.DataFrame(rows)


def _has_ranking(frame: pd.DataFrame) -> pd.Series:
    """Return whether each row contains an official exact rank or rank band."""

    numeric_rank = pd.to_numeric(frame["rank"], errors="coerce")
    band = frame["rank_band"].fillna("").astype(str).str.strip()
    return numeric_rank.notna() | band.ne("")


def _ranking_support_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    """Return held-out rows supported by the ranking representation in training."""

    train_exact = pd.to_numeric(train["rank"], errors="coerce").dropna()
    exact_supported = train_exact.nunique() >= 2
    train_bands = set(
        train["rank_band"]
        .fillna("")
        .astype(str)
        .str.strip()
        .loc[lambda s: s.ne("")]
    )

    test_exact = pd.to_numeric(test["rank"], errors="coerce")
    test_band = test["rank_band"].fillna("").astype(str).str.strip()
    exact_rows = test_exact.notna()
    band_rows = test_band.ne("")

    supported = pd.Series(False, index=test.index, dtype=bool)
    if exact_supported:
        supported.loc[exact_rows] = True
    supported.loc[band_rows] = test_band.loc[band_rows].isin(train_bands)
    return supported


def _structural_support_mask(train: pd.DataFrame, test: pd.DataFrame) -> pd.Series:
    """Return rows whose registered structural categories occur in training."""

    train_programmes = set(train["programme_code"].astype(str))
    train_years = set(train["year"].astype(str))
    return (
        test["programme_code"].astype(str).isin(train_programmes)
        & test["year"].astype(str).isin(train_years)
    )


def _design_schema(
    frame: pd.DataFrame,
    *,
    include_ranking: bool,
) -> DesignSchema:
    """Freeze categorical levels from one training fold."""

    programme_levels = tuple(sorted(frame["programme_code"].astype(str).unique()))
    year_levels = tuple(sorted(frame["year"].astype(str).unique()))
    ranking_band_levels: tuple[str, ...] = ()
    if include_ranking:
        rank_band = frame["rank_band"].fillna("").astype(str).str.strip()
        encoded_band = rank_band.where(rank_band.ne(""), "__exact_rank__")
        ranking_band_levels = tuple(sorted(encoded_band.unique()))
    return DesignSchema(
        programme_levels=programme_levels,
        year_levels=year_levels,
        ranking_band_levels=ranking_band_levels,
    )


def _categorical_dummies(
    values: pd.Series,
    *,
    levels: tuple[str, ...],
    prefix: str,
) -> pd.DataFrame:
    """Encode values against training-owned levels and a fixed first reference."""

    text = values.astype(str)
    unknown = sorted(set(text.unique()) - set(levels))
    if unknown:
        raise ValueError(
            f"held-out {prefix} levels are absent from training: {unknown}"
        )
    categorical = pd.Categorical(text, categories=list(levels), ordered=True)
    dummies = pd.get_dummies(
        categorical,
        prefix=prefix,
        drop_first=True,
        dtype=float,
    )
    dummies.index = values.index
    return dummies


def leave_one_parent_out_comparison(
    frame: pd.DataFrame,
    *,
    outcome: str,
    include_demand: bool,
) -> LopoComparisonResult:
    """Compare baseline and ranking models on identical supported LOPO rows.

    Both models are trained on the same provider-ranked rows. A held-out row is
    scored only when its programme/year categories occur in training and its
    ranking representation is supported there. Unsupported rows are reported
    explicitly and are never mapped to a reference category.
    """

    required = (
        "programme_code",
        "year",
        "parent_institution_id",
        "applicants_per_vacancy",
        "rank",
        "rank_band",
        outcome,
    )
    require_columns(frame, required)

    data = frame.dropna(
        subset=["programme_code", "year", "parent_institution_id", outcome]
    ).copy()
    data = data.loc[_has_ranking(data)].copy()
    if include_demand:
        data = data.loc[data["applicants_per_vacancy"] > 0].copy()

    eligible_rows = int(len(data))
    eligible_parents = int(data["parent_institution_id"].astype(str).nunique())
    baseline_predictions: list[float] = []
    ranking_predictions: list[float] = []
    observed: list[float] = []
    unsupported_ranking_rows = 0
    unsupported_structural_rows = 0
    supported_parent_ids: set[str] = set()

    for parent in sorted(data["parent_institution_id"].astype(str).unique()):
        test = data.loc[data["parent_institution_id"].astype(str) == parent]
        train = data.loc[data["parent_institution_id"].astype(str) != parent]
        if test.empty or train.empty:
            continue

        ranking_support = _ranking_support_mask(train, test)
        structural_support = _structural_support_mask(train, test)
        unsupported_ranking_rows += int((~ranking_support).sum())
        unsupported_structural_rows += int(
            (ranking_support & ~structural_support).sum()
        )
        support_mask = ranking_support & structural_support
        supported_test = test.loc[support_mask].copy()
        if supported_test.empty:
            continue
        supported_parent_ids.add(parent)

        baseline_schema = _design_schema(train, include_ranking=False)
        baseline_train_design = _design(
            train,
            include_demand=include_demand,
            include_ranking=False,
            schema=baseline_schema,
        )
        baseline_test_design = _design(
            supported_test,
            include_demand=include_demand,
            include_ranking=False,
            schema=baseline_schema,
            columns=list(baseline_train_design.columns),
        )
        ranking_schema = _design_schema(train, include_ranking=True)
        ranking_train_design = _design(
            train,
            include_demand=include_demand,
            include_ranking=True,
            schema=ranking_schema,
        )
        ranking_test_design = _design(
            supported_test,
            include_demand=include_demand,
            include_ranking=True,
            schema=ranking_schema,
            columns=list(ranking_train_design.columns),
        )

        baseline_model = sm.OLS(
            train[outcome].astype(float), baseline_train_design
        ).fit()
        ranking_model = sm.OLS(
            train[outcome].astype(float), ranking_train_design
        ).fit()
        baseline_predictions.extend(
            baseline_model.predict(baseline_test_design).tolist()
        )
        ranking_predictions.extend(
            ranking_model.predict(ranking_test_design).tolist()
        )
        observed.extend(supported_test[outcome].astype(float).tolist())

    if not observed:
        raise ValueError(
            "leave-one-parent-out comparison produced no supported test observations"
        )

    observed_array = np.asarray(observed)
    baseline_residual = observed_array - np.asarray(baseline_predictions)
    ranking_residual = observed_array - np.asarray(ranking_predictions)
    unsupported_rows = unsupported_ranking_rows + unsupported_structural_rows
    return LopoComparisonResult(
        baseline_rmse=float(np.sqrt(np.mean(baseline_residual**2))),
        ranking_rmse=float(np.sqrt(np.mean(ranking_residual**2))),
        baseline_mae=float(np.mean(np.abs(baseline_residual))),
        ranking_mae=float(np.mean(np.abs(ranking_residual))),
        eligible_rows=eligible_rows,
        eligible_parents=eligible_parents,
        supported_rows=int(len(observed)),
        unsupported_rows=unsupported_rows,
        supported_parents=len(supported_parent_ids),
        unsupported_ranking_rows=unsupported_ranking_rows,
        unsupported_structural_rows=unsupported_structural_rows,
    )


def leave_one_parent_out_rmse(
    frame: pd.DataFrame,
    *,
    outcome: str,
    include_demand: bool,
    include_ranking: bool,
) -> float:
    """Return LOPO RMSE for one model, preserving backward compatibility."""

    required = [
        "programme_code",
        "year",
        "parent_institution_id",
        "applicants_per_vacancy",
        outcome,
    ]
    if include_ranking:
        required.extend(("rank", "rank_band"))
    require_columns(frame, tuple(required))

    data = frame.dropna(
        subset=["programme_code", "year", "parent_institution_id", outcome]
    ).copy()
    if include_demand:
        data = data.loc[data["applicants_per_vacancy"] > 0].copy()
    if include_ranking:
        data = data.loc[_has_ranking(data)].copy()

    predictions: list[float] = []
    observed: list[float] = []
    for parent in sorted(data["parent_institution_id"].astype(str).unique()):
        test = data.loc[data["parent_institution_id"].astype(str) == parent]
        train = data.loc[data["parent_institution_id"].astype(str) != parent]
        if test.empty or train.empty:
            continue

        structural_support = _structural_support_mask(train, test)
        if include_ranking:
            ranking_support = _ranking_support_mask(train, test)
            test = test.loc[structural_support & ranking_support].copy()
        else:
            test = test.loc[structural_support].copy()
        if test.empty:
            continue

        schema = _design_schema(train, include_ranking=include_ranking)
        train_design = _design(
            train,
            include_demand=include_demand,
            include_ranking=include_ranking,
            schema=schema,
        )
        test_design = _design(
            test,
            include_demand=include_demand,
            include_ranking=include_ranking,
            schema=schema,
            columns=list(train_design.columns),
        )
        model = sm.OLS(train[outcome].astype(float), train_design).fit()
        predictions.extend(model.predict(test_design).tolist())
        observed.extend(test[outcome].astype(float).tolist())
    if not observed:
        raise ValueError(
            "leave-one-parent-out validation produced no supported test observations"
        )
    residual = np.asarray(observed) - np.asarray(predictions)
    return float(np.sqrt(np.mean(residual**2)))


def _design(
    frame: pd.DataFrame,
    *,
    include_demand: bool,
    include_ranking: bool,
    schema: DesignSchema | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Build a model matrix using fixed training-owned categorical references."""

    schema = schema or _design_schema(frame, include_ranking=include_ranking)
    data = pd.DataFrame(index=frame.index)

    programme = _categorical_dummies(
        frame["programme_code"],
        levels=schema.programme_levels,
        prefix="programme",
    )
    year = _categorical_dummies(
        frame["year"].astype(str),
        levels=schema.year_levels,
        prefix="year",
    )
    data = pd.concat([data, programme, year], axis=1)

    if include_demand:
        data["log_applicants_per_vacancy"] = np.log(
            frame["applicants_per_vacancy"].astype(float)
        )

    if include_ranking:
        exact_rank = pd.to_numeric(frame["rank"], errors="coerce")
        data["ranking_exact_observed"] = exact_rank.notna().astype(float)
        data["ranking_exact"] = exact_rank.fillna(0.0).astype(float)

        rank_band = frame["rank_band"].fillna("").astype(str).str.strip()
        encoded_band = rank_band.where(rank_band.ne(""), "__exact_rank__")
        band_dummies = _categorical_dummies(
            encoded_band,
            levels=schema.ranking_band_levels,
            prefix="ranking_band",
        )
        data = pd.concat([data, band_dummies], axis=1)

    data = sm.add_constant(data, has_constant="add")
    if columns is not None:
        data = data.reindex(columns=columns, fill_value=0.0)
    return data.astype(float)
