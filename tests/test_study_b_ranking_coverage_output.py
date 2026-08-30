"""Release-data tests for Study B provider-specific ranking coverage."""
from __future__ import annotations

from math import isclose
from pathlib import Path

import pandas as pd

from scripts.build_study_b_ranking_coverage import build

ROOT = Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "results" / "study_b" / "ranking_coverage.csv"


def test_ranking_coverage_output_rebuilds_exactly() -> None:
    """Rebuild the coverage table from committed DGES shards and audit inputs."""
    expected = pd.read_csv(COMMITTED).sort_values(
        ["provider", "admission_year"]
    ).reset_index(drop=True)
    observed = build().sort_values(
        ["provider", "admission_year"]
    ).reset_index(drop=True)
    pd.testing.assert_frame_equal(observed, expected, check_dtype=False)


def test_registered_provider_row_denominators() -> None:
    """Freeze the exact provider-specific modelling denominators before fitting."""
    coverage = pd.read_csv(COMMITTED)
    assert set(coverage["eligible_parent_institutions"]) == {13}
    assert set(coverage["eligible_rows"]) == {52}

    qs = coverage.loc[coverage["provider"] == "QS"].sort_values("admission_year")
    assert qs["verified_ranked_parent_institutions"].tolist() == [6, 6, 6]
    assert qs["verified_ranked_rows"].tolist() == [18, 18, 18]

    the = coverage.loc[
        coverage["provider"] == "Times Higher Education"
    ].sort_values("admission_year")
    assert the["verified_ranked_parent_institutions"].tolist() == [11, 11, 11]
    assert the["verified_ranked_rows"].tolist() == [42, 42, 42]
    assert the["unresolved_parent_institutions"].tolist() == [1, 1, 1]
    assert the["unresolved_rows"].tolist() == [5, 5, 5]

    arwu = coverage.loc[coverage["provider"] == "ARWU"].sort_values("admission_year")
    assert arwu["verified_ranked_parent_institutions"].tolist() == [5, 4, 6]
    assert arwu["verified_ranked_rows"].tolist() == [16, 13, 18]

    assert isclose(float(qs.iloc[0]["verified_row_coverage"]), 18 / 52)
    assert isclose(float(the.iloc[0]["verified_row_coverage"]), 42 / 52)
    assert isclose(float(arwu.iloc[0]["verified_row_coverage"]), 16 / 52)
