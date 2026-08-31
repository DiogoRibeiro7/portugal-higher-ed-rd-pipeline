"""Unit tests for the registered Study B ranking design."""
from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_b_rankings import (
    _design,
    _design_schema,
    _ranking_support_mask,
    build_ranking_coverage,
    leave_one_parent_out_comparison,
    leave_one_parent_out_rmse,
    validate_ranking_rows,
)


def _rankings() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "admission_year": year,
                "provider": "QS",
                "parent_institution_id": parent,
                "publication_date": f"{year}-06-01",
                "application_deadline": f"{year}-08-01",
                "rank": rank,
                "rank_band": None,
            }
            for year in (2018, 2019, 2020)
            for parent, rank in (("u1", 1), ("u2", 2), ("u3", 3))
        ]
    )


def _panel() -> pd.DataFrame:
    rows = []
    for year in (2018, 2019, 2020):
        for programme in ("9081", "9119"):
            for index, parent in enumerate(("u1", "u2", "u3"), start=1):
                rows.append(
                    {
                        "year": year,
                        "programme_code": programme,
                        "parent_institution_id": parent,
                        "applicants_per_vacancy": 1.0
                        + index
                        + 0.1 * (year - 2018),
                        "rank": float(index) if parent != "u3" else None,
                        "rank_band": "501-600" if parent == "u3" else None,
                        "last_placed_general_contingent_grade": (
                            120.0 + 4 * index + year - 2018
                        ),
                        "mean_application_grade_placed": (
                            130.0 + 3 * index + year - 2018
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _band_panel() -> pd.DataFrame:
    rows = []
    bands = {"u1": "401-500", "u2": "401-500", "u3": "501-600"}
    for year in (2018, 2019, 2020):
        for programme in ("9081", "9119"):
            for index, parent in enumerate(("u1", "u2", "u3"), start=1):
                rows.append(
                    {
                        "year": year,
                        "programme_code": programme,
                        "parent_institution_id": parent,
                        "applicants_per_vacancy": 1.0 + index,
                        "rank": None,
                        "rank_band": bands[parent],
                        "last_placed_general_contingent_grade": 120.0 + 4 * index,
                        "mean_application_grade_placed": 130.0 + 3 * index,
                    }
                )
    return pd.DataFrame(rows)


def test_ranking_rows_reject_post_deadline_publication() -> None:
    rows = _rankings()
    rows.loc[0, "publication_date"] = "2018-09-01"
    with pytest.raises(ValueError, match="after the application deadline"):
        validate_ranking_rows(rows)


def test_ranking_rows_reject_exact_rank_and_band_together() -> None:
    rows = _rankings()
    rows.loc[0, "rank_band"] = "1-10"
    with pytest.raises(ValueError, match="exact rank or rank band"):
        validate_ranking_rows(rows)


def test_ranking_rows_reject_nonpositive_exact_rank() -> None:
    rows = _rankings()
    rows.loc[0, "rank"] = 0
    with pytest.raises(ValueError, match="strictly positive"):
        validate_ranking_rows(rows)


def test_coverage_reports_ranked_rows_without_imputation() -> None:
    rankings = _rankings()
    rankings = rankings.loc[
        ~(
            (rankings["admission_year"] == 2020)
            & (rankings["parent_institution_id"] == "u3")
        )
    ]
    coverage = build_ranking_coverage(_panel(), rankings, provider="QS")
    row = coverage.loc[coverage["year"] == 2020].iloc[0]
    assert row["eligible_parent_institutions"] == 3
    assert row["ranked_parent_institutions"] == 2
    assert row["eligible_rows"] == 6
    assert row["ranked_rows"] == 4


def test_rank_bands_are_categorical_not_numeric_midpoints() -> None:
    design = _design(
        _panel(),
        include_demand=False,
        include_ranking=True,
    )
    assert "ranking_exact" in design.columns
    assert "ranking_exact_observed" in design.columns
    assert any(column.startswith("ranking_band_") for column in design.columns)
    assert "ranking_score" not in design.columns

    band_rows = _panel()["rank_band"].notna()
    assert (design.loc[band_rows, "ranking_exact"] == 0.0).all()
    assert (design.loc[band_rows, "ranking_exact_observed"] == 0.0).all()


def test_test_design_uses_training_reference_levels() -> None:
    train = pd.DataFrame(
        {
            "programme_code": ["9081", "9119", "9081", "9119"],
            "year": [2018, 2018, 2019, 2020],
            "applicants_per_vacancy": [2.0, 3.0, 4.0, 5.0],
            "rank": [None, None, None, None],
            "rank_band": ["401-500", "501-600", "401-500", "501-600"],
        }
    )
    test = pd.DataFrame(
        {
            "programme_code": ["9119"],
            "year": [2019],
            "applicants_per_vacancy": [6.0],
            "rank": [None],
            "rank_band": ["501-600"],
        },
        index=[99],
    )
    schema = _design_schema(train, include_ranking=True)
    train_design = _design(
        train,
        include_demand=False,
        include_ranking=True,
        schema=schema,
    )
    test_design = _design(
        test,
        include_demand=False,
        include_ranking=True,
        schema=schema,
        columns=list(train_design.columns),
    )
    assert test_design.loc[99, "programme_9119"] == 1.0
    assert test_design.loc[99, "year_2019"] == 1.0
    assert test_design.loc[99, "ranking_band_501-600"] == 1.0


def test_unseen_structural_level_fails_closed() -> None:
    train = _band_panel().loc[lambda x: x["programme_code"] == "9081"]
    test = _band_panel().loc[lambda x: x["programme_code"] == "9119"].iloc[:1]
    schema = _design_schema(train, include_ranking=True)
    with pytest.raises(ValueError, match="held-out programme levels"):
        _design(
            test,
            include_demand=False,
            include_ranking=True,
            schema=schema,
        )


def test_unseen_held_out_band_is_not_supported() -> None:
    panel = _band_panel()
    train = panel.loc[panel["parent_institution_id"].isin(["u1", "u2"])]
    test = panel.loc[panel["parent_institution_id"] == "u3"]
    support = _ranking_support_mask(train, test)
    assert not support.any()


def test_paired_lopo_comparison_uses_only_identical_supported_rows() -> None:
    panel = _band_panel()
    result = leave_one_parent_out_comparison(
        panel,
        outcome="last_placed_general_contingent_grade",
        include_demand=False,
    )
    assert result.eligible_rows == len(panel)
    assert result.eligible_parents == 3
    assert result.supported_rows == 12
    assert result.unsupported_rows == 6
    assert result.supported_parents == 2
    assert result.baseline_rmse >= 0
    assert result.ranking_rmse >= 0
    assert result.baseline_mae >= 0
    assert result.ranking_mae >= 0


def test_leave_one_parent_out_runs_for_registered_model_sequence() -> None:
    panel = _band_panel()
    baseline = leave_one_parent_out_rmse(
        panel,
        outcome="last_placed_general_contingent_grade",
        include_demand=False,
        include_ranking=False,
    )
    ranking = leave_one_parent_out_rmse(
        panel,
        outcome="last_placed_general_contingent_grade",
        include_demand=False,
        include_ranking=True,
    )
    demand = leave_one_parent_out_rmse(
        panel,
        outcome="last_placed_general_contingent_grade",
        include_demand=True,
        include_ranking=False,
    )
    demand_ranking = leave_one_parent_out_rmse(
        panel,
        outcome="last_placed_general_contingent_grade",
        include_demand=True,
        include_ranking=True,
    )
    assert all(
        value >= 0
        for value in (baseline, ranking, demand, demand_ranking)
    )
