"""Release-data contracts for the v0.3.3 matched-course pilot."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pt_he_pipeline.study_b_course_pilot import (
    add_course_pilot_metrics,
    build_cross_section_associations,
    build_leave_one_year_out,
    build_nested_model_summary,
    reconcile_overlapping_sources,
    summarise_leave_one_year_out,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "data/curated/dges/course_9119_engineering_informatics_2018_2020_source_rows.csv"
)


def _release_panel() -> pd.DataFrame:
    source_rows = pd.read_csv(
        SOURCE,
        dtype={"programme_code": str, "institution_code": str},
    )
    canonical, _ = reconcile_overlapping_sources(source_rows)
    return add_course_pilot_metrics(canonical)


def test_release_source_has_exact_overlap_and_balanced_panel() -> None:
    source_rows = pd.read_csv(
        SOURCE,
        dtype={"programme_code": str, "institution_code": str},
    )
    canonical, reconciliation = reconcile_overlapping_sources(source_rows)

    assert len(source_rows) == 92
    assert len(canonical) == 69
    assert set(canonical["year"]) == {2018, 2019, 2020}
    assert canonical.groupby("year")["institution_code"].nunique().tolist() == [23, 23, 23]
    overlap = reconciliation.loc[reconciliation["year"] == 2019]
    assert len(overlap) == 23
    assert (overlap["source_document_count"] == 2).all()


def test_release_aveiro_values_match_registered_source_transcription() -> None:
    panel = _release_panel().set_index(["year", "institution_code"])

    row_2019 = panel.loc[(2019, "0300")]
    assert row_2019["vacancies"] == 60
    assert row_2019["applicants"] == 689
    assert row_2019["first_choice_applicants"] == 146
    assert row_2019["placements"] == 60
    assert row_2019["last_placed_general_contingent_grade"] == pytest.approx(162.5)
    assert row_2019["mean_application_grade_placed"] == pytest.approx(169.3)

    row_2020 = panel.loc[(2020, "0300")]
    assert row_2020["applicants"] == 839
    assert row_2020["last_placed_general_contingent_grade"] == pytest.approx(177.5)


def test_release_cross_section_r_squared_is_not_near_complete_in_every_year() -> None:
    associations = build_cross_section_associations(_release_panel()).set_index(
        ["year", "outcome", "demand_variable"]
    )
    demand = "applicants_per_vacancy"
    cutoff = "last_placed_general_contingent_grade"
    mean_grade = "mean_application_grade_placed"

    assert associations.loc[(2018, cutoff, demand), "r_squared"] == pytest.approx(
        0.6468740356
    )
    assert associations.loc[(2019, cutoff, demand), "r_squared"] == pytest.approx(
        0.5585645074
    )
    assert associations.loc[(2020, cutoff, demand), "r_squared"] == pytest.approx(
        0.7433505154
    )
    assert associations.loc[(2018, mean_grade, demand), "r_squared"] == pytest.approx(
        0.4983491849
    )
    assert associations.loc[(2020, mean_grade, demand), "r_squared"] == pytest.approx(
        0.7658243022
    )


def test_release_nested_models_show_demand_and_persistent_institution_structure() -> None:
    models = build_nested_model_summary(_release_panel()).set_index(["outcome", "model"])
    cutoff = "last_placed_general_contingent_grade"
    mean_grade = "mean_application_grade_placed"

    assert models.loc[(cutoff, "year_plus_demand"), "r_squared"] == pytest.approx(
        0.6741735044
    )
    assert models.loc[
        (cutoff, "institution_year_plus_demand"), "r_squared"
    ] == pytest.approx(0.9731099963)
    assert models.loc[
        (cutoff, "institution_year_plus_demand"),
        "incremental_r_squared_vs_structure",
    ] == pytest.approx(0.01966598341)

    assert models.loc[(mean_grade, "year_plus_demand"), "r_squared"] == pytest.approx(
        0.6786271323
    )
    assert models.loc[
        (mean_grade, "institution_year_plus_demand"),
        "incremental_r_squared_vs_structure",
    ] == pytest.approx(0.01763202597)


def test_release_demand_improves_leave_one_year_out_prediction() -> None:
    loyo = build_leave_one_year_out(_release_panel())
    summary = summarise_leave_one_year_out(loyo).set_index(["outcome", "model"])
    cutoff = "last_placed_general_contingent_grade"
    mean_grade = "mean_application_grade_placed"

    assert summary.loc[(cutoff, "institution_year"), "mean_rmse"] == pytest.approx(
        9.097042251,
        abs=1e-6,
    )
    assert summary.loc[
        (cutoff, "institution_year_plus_demand"), "mean_rmse"
    ] == pytest.approx(7.490430474, abs=1e-6)
    assert summary.loc[(mean_grade, "institution_year"), "mean_rmse"] == pytest.approx(
        6.513501238,
        abs=1e-6,
    )
    assert summary.loc[
        (mean_grade, "institution_year_plus_demand"), "mean_rmse"
    ] == pytest.approx(5.132539129, abs=1e-6)
