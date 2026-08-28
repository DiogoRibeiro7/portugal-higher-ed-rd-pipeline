"""Unit tests for the Study B matched-course pilot."""

from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_b_course_pilot import (
    MatchedCoursePolicy,
    add_course_pilot_metrics,
    build_cross_section_associations,
    build_leave_one_year_out,
    build_nested_model_summary,
    reconcile_overlapping_sources,
    summarise_leave_one_year_out,
    validate_source_rows,
)


def _source_rows() -> pd.DataFrame:
    """Return the smallest valid two-source overlap fixture."""

    institutions = [f"{index:04d}" for index in range(1, 24)]
    rows: list[dict[str, object]] = []
    for source_document_year, years in ((2019, (2018, 2019)), (2020, (2019, 2020))):
        for year in years:
            for position, institution_code in enumerate(institutions, start=1):
                vacancies = 20 + position
                applicants = vacancies * 2 + year - 2018 + position
                rows.append(
                    {
                        "source_document_year": source_document_year,
                        "source_url": "https://example.invalid/source.pdf",
                        "source_pages": "C1-C2",
                        "source_section": "9119 Engenharia Informática [Licenciatura]",
                        "source_type": "DGES StatsCurso comparative first-phase table",
                        "provider_bytes_bundled": False,
                        "year": year,
                        "programme_code": "9119",
                        "programme_name": "Engenharia Informática",
                        "degree": "Licenciatura",
                        "institution_code": institution_code,
                        "institution_name": f"Institution {position}",
                        "vacancies": vacancies,
                        "applicants": applicants,
                        "first_choice_applicants": vacancies,
                        "placements": vacancies,
                        "first_choice_placements": max(vacancies - 2, 0),
                        "last_placed_general_contingent_grade": 100.0 + position + year - 2018,
                        "mean_application_grade_placed": 110.0 + position + year - 2018,
                        "mean_entrance_exam_grade_placed": 105.0 + position + year - 2018,
                        "mean_secondary_grade_placed": 115.0 + position + year - 2018,
                    }
                )
    return pd.DataFrame(rows)


def test_validate_source_rows_accepts_registered_overlap() -> None:
    source_rows = _source_rows()
    validate_source_rows(source_rows)


def test_reconciliation_builds_69_row_balanced_panel() -> None:
    canonical, reconciliation = reconcile_overlapping_sources(_source_rows())
    assert len(canonical) == 69
    assert canonical.groupby("year")["institution_code"].nunique().tolist() == [23, 23, 23]
    assert len(reconciliation) == 69
    overlap = reconciliation.loc[reconciliation["year"] == 2019]
    assert (overlap["source_document_count"] == 2).all()


def test_reconciliation_rejects_source_disagreement() -> None:
    source_rows = _source_rows()
    mask = (
        (source_rows["source_document_year"] == 2020)
        & (source_rows["year"] == 2019)
        & (source_rows["institution_code"] == "0001")
    )
    source_rows.loc[mask, "applicants"] += 1
    with pytest.raises(ValueError, match="overlapping DGES source rows disagree"):
        reconcile_overlapping_sources(source_rows)


def test_metrics_preserve_possible_tie_place_occupancy_above_one() -> None:
    canonical, _ = reconcile_overlapping_sources(_source_rows())
    canonical.loc[0, "placements"] = canonical.loc[0, "vacancies"] + 1
    metrics = add_course_pilot_metrics(canonical)
    assert float(metrics.loc[0, "occupancy_rate"]) > 1.0


def test_model_builders_return_registered_specifications() -> None:
    canonical, _ = reconcile_overlapping_sources(_source_rows())
    panel = add_course_pilot_metrics(canonical)
    associations = build_cross_section_associations(panel)
    models = build_nested_model_summary(panel)
    loyo = build_leave_one_year_out(panel)
    summary = summarise_leave_one_year_out(loyo)

    assert len(associations) == 12
    assert set(models["model"]) == {
        "year",
        "year_plus_demand",
        "institution_year",
        "institution_year_plus_demand",
    }
    assert len(loyo) == 24
    assert len(summary) == 8
    assert (summary["held_out_years"] == 3).all()


def test_policy_years_are_explicitly_consecutive() -> None:
    policy = MatchedCoursePolicy(first_year=2018, last_year=2020)
    assert policy.expected_years == (2018, 2019, 2020)
