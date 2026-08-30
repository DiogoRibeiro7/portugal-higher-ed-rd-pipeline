"""Regression tests for the historical ranking coverage audit status table."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "curated" / "rankings" / "study_b_provider_coverage_status.csv"


def _load() -> pd.DataFrame:
    """Load the committed provider/year coverage-status table."""

    return pd.read_csv(COVERAGE)


def test_coverage_status_has_one_row_per_provider_year() -> None:
    """Every registered provider/year cell must appear exactly once."""

    frame = _load()
    assert len(frame) == 9
    assert not frame.duplicated(["provider", "admission_year"]).any()
    assert set(frame["provider"]) == {"QS", "Times Higher Education", "ARWU"}
    assert set(frame["admission_year"]) == {2018, 2019, 2020}


def test_qs_core_coverage_is_stable_across_frozen_editions() -> None:
    """The verified QS overall-ranking core is six registered parents in each year."""

    frame = _load()
    qs = frame.loc[frame["provider"] == "QS"]
    expected = {"ulisboa", "uporto", "nova", "uc", "ua", "uminho"}
    for value in qs["verified_parent_ids"]:
        assert set(str(value).split("|")) == expected


def test_arwu_remains_unresolved_not_unranked() -> None:
    """Missing historical ARWU verification must not be recoded as non-coverage."""

    frame = _load()
    arwu = frame.loc[frame["provider"] == "ARWU"]
    assert set(arwu["coverage_status"]) == {"unresolved"}
    assert arwu["verified_parent_ids"].isna().all()
    assert arwu["unresolved_parent_ids"].notna().all()


def test_the_2020_verified_set_is_broader_than_qs_2020() -> None:
    """The recovered THE 2020 parent set must remain broader than QS 2020."""

    frame = _load()
    the = frame.loc[
        (frame["provider"] == "Times Higher Education")
        & (frame["admission_year"] == 2020),
        "verified_parent_ids",
    ].iloc[0]
    qs = frame.loc[
        (frame["provider"] == "QS") & (frame["admission_year"] == 2020),
        "verified_parent_ids",
    ].iloc[0]
    assert len(set(str(the).split("|"))) > len(set(str(qs).split("|")))
