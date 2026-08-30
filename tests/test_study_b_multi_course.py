"""Tests for the registered Study B multi-course extension."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pt_he_pipeline.study_b_multi_course import (
    MultiCoursePolicy,
    RegisteredProgramme,
    add_metrics,
    build_model_panel,
    build_stable_panel,
    programme_year_associations,
    reconcile_sources,
    summarise_associations,
    validate_registry,
)

PROGRAMMES = (
    RegisteredProgramme("9119", "Engenharia Informática"),
    RegisteredProgramme("9147", "Gestão"),
)
POLICY = MultiCoursePolicy(min_stable_institutions=6)


def _rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for p_index, programme in enumerate(PROGRAMMES):
        for source_year, years in ((2019, (2018, 2019)), (2020, (2019, 2020))):
            for year in years:
                for position in range(1, 8):
                    institution = f"{position:04d}"
                    if position == 7 and year != 2019:
                        continue
                    vacancies = 20 + position
                    applicants = vacancies * 2 + position + 3 * (year - 2018)
                    base = 105 + 5 * p_index + position
                    rows.append(
                        {
                            "source_document_year": source_year,
                            "programme_name": programme.name,
                            "degree": programme.degree,
                            "year": year,
                            "programme_code": programme.code,
                            "institution_code": institution,
                            "vacancies": vacancies,
                            "applicants": applicants,
                            "first_choice_applicants": applicants // 3,
                            "placements": vacancies,
                            "first_choice_placements": vacancies // 2,
                            "last_placed_general_contingent_grade": (
                                base + 2.5 * np.log(applicants / vacancies)
                            ),
                            "mean_application_grade_placed": (
                                base + 10 + 3.0 * np.log(applicants / vacancies)
                            ),
                            "mean_entrance_exam_grade_placed": base + 5,
                            "mean_secondary_grade_placed": base + 15,
                        }
                    )
    return pd.DataFrame(rows)


def test_registry_rejects_duplicate_codes() -> None:
    with pytest.raises(ValueError, match="non-empty and unique"):
        validate_registry(
            (
                RegisteredProgramme("9119", "A"),
                RegisteredProgramme("9119", "B"),
            )
        )


def test_reconciliation_and_stable_coverage() -> None:
    canonical, audit = reconcile_sources(_rows(), programmes=PROGRAMMES, policy=POLICY)
    panel, coverage = build_stable_panel(
        canonical,
        audit,
        programmes=PROGRAMMES,
        policy=POLICY,
    )
    assert len(panel) == 2 * 6 * 3
    assert (coverage["stable_institutions"] == 6).all()
    assert (coverage["institutions_observed_any_year"] == 7).all()


def test_reconciliation_rejects_disagreement() -> None:
    rows = _rows()
    mask = (
        (rows["source_document_year"] == 2020)
        & (rows["year"] == 2019)
        & (rows["programme_code"] == "9147")
        & (rows["institution_code"] == "0001")
    )
    rows.loc[mask, "applicants"] += 1
    with pytest.raises(ValueError, match="overlapping source rows disagree"):
        reconcile_sources(rows, programmes=PROGRAMMES, policy=POLICY)


def test_model_attrition_is_reported_separately() -> None:
    canonical, audit = reconcile_sources(_rows(), programmes=PROGRAMMES, policy=POLICY)
    panel, _ = build_stable_panel(canonical, audit, programmes=PROGRAMMES, policy=POLICY)
    metrics = add_metrics(panel, policy=POLICY)
    mask = (
        (metrics["programme_code"] == "9147")
        & (metrics["institution_code"] == "0001")
    )
    metrics.loc[mask, "last_placed_general_contingent_grade"] = np.nan
    model, coverage = build_model_panel(metrics, policy=POLICY)
    row = coverage.set_index("programme_code").loc["9147"]
    assert int(row["excluded_institutions"]) == 1
    assert not (
        (model["programme_code"] == "9147")
        & (model["institution_code"] == "0001")
    ).any()


def test_association_distribution_is_returned() -> None:
    canonical, audit = reconcile_sources(_rows(), programmes=PROGRAMMES, policy=POLICY)
    panel, _ = build_stable_panel(canonical, audit, programmes=PROGRAMMES, policy=POLICY)
    model, _ = build_model_panel(add_metrics(panel, policy=POLICY), policy=POLICY)
    associations = programme_year_associations(model)
    summary = summarise_associations(associations)
    assert len(associations) == 2 * 3 * 2
    assert len(summary) == 2
