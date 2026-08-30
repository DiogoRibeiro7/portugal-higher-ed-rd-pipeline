"""Unit tests for the registered Study B ranking design."""
from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_b_rankings import (
    build_ranking_coverage,
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
                        "applicants_per_vacancy": 1.0 + index + 0.1 * (year - 2018),
                        "ranking_score": float(index),
                        "last_placed_general_contingent_grade": 120.0 + 4 * index + year - 2018,
                        "mean_application_grade_placed": 130.0 + 3 * index + year - 2018,
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


def test_coverage_reports_ranked_rows_without_imputation() -> None:
    rankings = _rankings()
    rankings = rankings.loc[~((rankings["admission_year"] == 2020) & (rankings["parent_institution_id"] == "u3"))]
    coverage = build_ranking_coverage(_panel(), rankings, provider="QS")
    row = coverage.loc[coverage["year"] == 2020].iloc[0]
    assert row["eligible_parent_institutions"] == 3
    assert row["ranked_parent_institutions"] == 2
    assert row["eligible_rows"] == 6
    assert row["ranked_rows"] == 4


def test_leave_one_parent_out_runs_for_registered_model_sequence() -> None:
    panel = _panel()
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
    assert all(value >= 0 for value in (baseline, ranking, demand, demand_ranking))
