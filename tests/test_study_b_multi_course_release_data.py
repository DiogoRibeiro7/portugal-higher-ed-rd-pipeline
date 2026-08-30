"""Release-data contracts for the registered Study B multi-course layer."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from pt_he_pipeline.study_b_multi_course import (
    MultiCoursePolicy,
    RegisteredProgramme,
    add_metrics,
    build_model_panel,
    build_stable_panel,
    programme_year_associations,
    reconcile_sources,
    summarise_associations,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated" / "dges"
PROGRAMMES = (
    RegisteredProgramme("9081", "Economia"),
    RegisteredProgramme("9119", "Engenharia Informática"),
    RegisteredProgramme("9147", "Gestão"),
    RegisteredProgramme("9219", "Psicologia"),
    RegisteredProgramme("9500", "Enfermagem"),
)
POLICY = MultiCoursePolicy(
    first_year=2018,
    last_year=2020,
    overlap_year=2019,
    min_stable_institutions=6,
)
SOURCE_FILES = (
    "course_9081_economics_2018_2020_source_rows.csv",
    "course_9119_engineering_informatics_2018_2020_source_rows.csv",
    "course_9147_management_2018_2020_source_rows_part1.csv",
    "course_9147_management_2018_2020_source_rows_part2a.csv",
    "course_9147_management_2018_2020_source_rows_part2b.csv",
    "course_9219_psychology_2018_2020_source_rows.csv",
    "course_9500_nursing_2018_2020_source_rows_part1.csv",
    "course_9500_nursing_2018_2020_source_rows_part2.csv",
    "course_9500_nursing_2018_2020_source_rows_part3.csv",
    "course_9500_nursing_2018_2020_source_rows_part4.csv",
)


def _rebuild() -> tuple[pd.DataFrame, ...]:
    """Rebuild the registered evidence from all committed source shards."""

    dtype = {"programme_code": str, "institution_code": str}
    source = pd.concat(
        [pd.read_csv(DATA / name, dtype=dtype) for name in SOURCE_FILES],
        ignore_index=True,
    )
    canonical, reconciliation = reconcile_sources(
        source,
        programmes=PROGRAMMES,
        policy=POLICY,
    )
    stable, coverage = build_stable_panel(
        canonical,
        reconciliation,
        programmes=PROGRAMMES,
        policy=POLICY,
    )
    stable = add_metrics(stable, policy=POLICY)
    model, attrition = build_model_panel(stable, policy=POLICY)
    associations = programme_year_associations(model)
    summary = summarise_associations(associations)
    return source, reconciliation, coverage, stable, attrition, model, associations, summary


def test_registered_sources_reconcile_and_clear_coverage_gate() -> None:
    """The frozen five-programme source set must pass every coverage gate."""

    source, reconciliation, coverage, stable, attrition, model, _, _ = _rebuild()
    assert len(source) == 348
    assert len(reconciliation) == 261
    overlap = reconciliation.loc[reconciliation["year"] == 2019]
    assert len(overlap) == 87
    assert (overlap["source_document_count"] == 2).all()

    counts = dict(zip(coverage["programme_code"], coverage["stable_institutions"], strict=True))
    assert counts == {"9081": 13, "9119": 23, "9147": 22, "9219": 8, "9500": 21}
    assert len(stable) == 261
    assert len(model) == 258
    excluded = attrition.loc[attrition["excluded_institutions"] > 0]
    assert excluded[["programme_code", "excluded_institutions"]].to_dict("records") == [
        {"programme_code": "9081", "excluded_institutions": 1}
    ]


def test_registered_multi_course_result_is_reproducible() -> None:
    """The primary association summary must remain numerically stable."""

    *_, associations, summary = _rebuild()
    cutoff = summary.loc[
        summary["outcome"] == "last_placed_general_contingent_grade"
    ].iloc[0]
    mean_grade = summary.loc[
        summary["outcome"] == "mean_application_grade_placed"
    ].iloc[0]

    assert np.isclose(cutoff["median_r_squared"], 0.5978495782435318)
    assert np.isclose(cutoff["q25_r_squared"], 0.4893143424852959)
    assert np.isclose(cutoff["q75_r_squared"], 0.66928588858857)
    assert np.isclose(cutoff["share_r_squared_ge_0_50"], 10 / 15)
    assert cutoff["share_r_squared_ge_0_80"] == 0.0

    assert np.isclose(mean_grade["median_r_squared"], 0.5518072303538704)
    assert np.isclose(mean_grade["q25_r_squared"], 0.4193373670572546)
    assert np.isclose(mean_grade["q75_r_squared"], 0.5799854551313132)
    assert np.isclose(mean_grade["share_r_squared_ge_0_50"], 9 / 15)
    assert mean_grade["share_r_squared_ge_0_80"] == 0.0
    assert (associations["log_demand_coefficient"] > 0).all()
    assert (associations["r_squared"] < 0.80).all()
