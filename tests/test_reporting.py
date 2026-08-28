from __future__ import annotations

import pandas as pd

from pt_he_pipeline.reporting import pair_coverage_report


def test_pair_coverage_report_exposes_missingness() -> None:
    frame = pd.DataFrame(
        {
            "year": [2025, 2025],
            "phase": [1, 1],
            "institution_id": ["A", "B"],
            "course_id": ["X", "Y"],
            "vacancies": [10, 20],
            "applicants": [30, 40],
            "first_choice_applicants": [5, 10],
            "placements": [10, 20],
            "mean_application_grade_placed": [150.0, None],
            "last_placed_general_contingent_grade": [145.0, None],
        }
    )
    report = pair_coverage_report(frame)
    assert report.loc[0, "rows"] == 2
    assert report.loc[0, "missing_mean_application_grade_placed_share"] == 0.5
