from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "study_b" / "multi_course_programme_year_associations.csv"
EXTENDED = (
    ROOT
    / "results"
    / "study_b"
    / "2021_extension"
    / "study_b_2018_2021_programme_year_associations.csv"
)
ATTRITION = (
    ROOT
    / "results"
    / "study_b"
    / "2021_extension"
    / "study_b_2018_2021_model_attrition.csv"
)


def test_pre_2021_associations_are_unchanged() -> None:
    dtype = {"programme_code": str}
    baseline = pd.read_csv(BASE, dtype=dtype).reset_index(drop=True)
    extended = pd.read_csv(EXTENDED, dtype=dtype)
    old = extended.loc[extended["year"] <= 2020].reset_index(drop=True)

    pd.testing.assert_frame_equal(old, baseline, check_exact=True, check_dtype=False)


def test_2021_cells_and_attrition_match_frozen_extension() -> None:
    dtype = {"programme_code": str}
    extended = pd.read_csv(EXTENDED, dtype=dtype)
    rows_2021 = extended.loc[extended["year"] == 2021]

    assert len(rows_2021) == 10
    assert set(rows_2021["programme_code"]) == {"9081", "9119", "9147", "9219", "9500"}
    assert set(rows_2021["outcome"]) == {
        "last_placed_general_contingent_grade",
        "mean_application_grade_placed",
    }
    assert (rows_2021["r_squared"] >= 0).all()
    assert (rows_2021["r_squared"] < 0.80).all()

    attrition = pd.read_csv(ATTRITION, dtype=dtype)
    observed = dict(
        zip(
            attrition["programme_code"],
            attrition["model_complete_institutions"],
            strict=True,
        )
    )
    assert observed == {"9081": 12, "9119": 23, "9147": 22, "9219": 8, "9500": 21}
