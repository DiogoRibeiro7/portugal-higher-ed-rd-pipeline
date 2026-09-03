"""Integrity tests for the Study B ranking coverage audit inputs."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONCORDANCE = ROOT / "data" / "curated" / "dges" / "study_b_parent_university_concordance.csv"
TIMING = ROOT / "data" / "curated" / "rankings" / "study_b_ranking_edition_timing.csv"


def test_parent_concordance_is_explicit_and_unique() -> None:
    frame = pd.read_csv(CONCORDANCE, dtype={"institution_code": str})
    assert not frame["institution_code"].duplicated().any()

    eligible = frame.loc[frame["ranking_eligible_parent"]]
    assert eligible["parent_institution_id"].notna().all()
    assert eligible["parent_institution_name"].notna().all()
    assert eligible["parent_institution_id"].nunique() == 13


def test_independent_nursing_schools_are_not_reassigned() -> None:
    frame = pd.read_csv(CONCORDANCE, dtype={"institution_code": str})
    independent = frame.set_index("institution_code").loc[["7001", "7002", "7003"]]
    assert (~independent["ranking_eligible_parent"]).all()
    assert independent["parent_institution_id"].isna().all()


def test_timing_has_one_frozen_edition_per_provider_and_year() -> None:
    frame = pd.read_csv(
        TIMING,
        parse_dates=["application_start", "application_deadline", "publication_date"],
    )
    assert len(frame) == 9
    assert set(frame["provider"]) == {"QS", "Times Higher Education", "ARWU"}
    assert set(frame["admission_year"]) == {2018, 2019, 2020}
    assert not frame.duplicated(["admission_year", "provider"]).any()
    assert (frame["publication_date"] <= frame["application_deadline"]).all()


def test_arwu_2020_preserves_registered_deadline_rule_edge_case() -> None:
    frame = pd.read_csv(
        TIMING,
        parse_dates=["application_start", "application_deadline", "publication_date"],
    )
    row = frame.loc[(frame["admission_year"] == 2020) & (frame["provider"] == "ARWU")].iloc[0]
    assert row["application_start"] < row["publication_date"] <= row["application_deadline"]
    assert row["timing_status"] == "eligible_before_deadline_but_after_open"
