"""Release-data checks for Study B ranking model comparisons."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "study_b" / "ranking_model_comparisons.csv"


def _load() -> pd.DataFrame:
    return pd.read_csv(RESULT)


def test_registered_ranking_output_has_fifteen_rows() -> None:
    frame = _load()
    assert len(frame) == 15
    assert set(frame["provider"]) == {"QS", "Times Higher Education", "ARWU"}
    assert frame.groupby("provider").size().to_dict() == {
        "ARWU": 5,
        "QS": 5,
        "Times Higher Education": 5,
    }


def test_ranking_deltas_are_exact_metric_differences() -> None:
    frame = _load()
    np.testing.assert_allclose(
        frame["delta_rmse"],
        frame["ranking_rmse"] - frame["baseline_rmse"],
    )
    np.testing.assert_allclose(
        frame["delta_mae"],
        frame["ranking_mae"] - frame["baseline_mae"],
    )


def test_lopo_support_counts_are_frozen_by_provider() -> None:
    frame = _load()
    expected = {
        "QS": (54, 30, 24, 4, 24, 0),
        "Times Higher Education": (116, 112, 4, 11, 4, 0),
        "ARWU": (47, 27, 20, 3, 17, 3),
    }
    for provider, values in expected.items():
        subset = frame.loc[frame["provider"] == provider]
        cols = [
            "eligible_rows",
            "supported_rows",
            "unsupported_rows",
            "supported_parents",
            "unsupported_ranking_rows",
            "unsupported_structural_rows",
        ]
        for column, expected_value in zip(cols, values, strict=True):
            assert set(subset[column]) == {expected_value}


def test_the_incremental_pattern_matches_registered_result() -> None:
    frame = _load()
    the = frame.loc[frame["provider"] == "Times Higher Education"]

    total = the.loc[the["comparison"] == "M0_vs_MR"].set_index("outcome")
    assert total.loc["last_placed_general_contingent_grade", "delta_rmse"] < 0
    assert total.loc["mean_application_grade_placed", "delta_rmse"] < 0

    conditional = the.loc[the["comparison"] == "MD_vs_MDR"].set_index("outcome")
    assert abs(
        conditional.loc["last_placed_general_contingent_grade", "delta_rmse"]
    ) < 0.05
    assert abs(
        conditional.loc["mean_application_grade_placed", "delta_rmse"]
    ) < 0.05
