"""Regression tests for the historical ranking coverage audit status table."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "curated" / "rankings" / "study_b_provider_coverage_status.csv"


def _load() -> pd.DataFrame:
    """Load the committed provider/year coverage-status table."""

    return pd.read_csv(COVERAGE)


def _ids(value: object) -> set[str]:
    """Parse one pipe-separated identifier field."""

    if pd.isna(value):
        return set()
    text = str(value).strip()
    return {item for item in text.split("|") if item} if text else set()


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
        assert _ids(value) == expected


def test_arwu_historical_parent_counts_are_resolved() -> None:
    """ARWU membership was resolved to verified 5/4/6-parent sets in PR #11."""

    frame = _load()
    arwu = frame.loc[frame["provider"] == "ARWU"].sort_values("admission_year")
    assert set(arwu["coverage_status"]) == {"verified_partial"}
    assert [len(_ids(value)) for value in arwu["verified_parent_ids"]] == [5, 4, 6]
    assert all(not _ids(value) for value in arwu["unresolved_parent_ids"])


def test_the_2018_and_2020_membership_counts_are_edition_specific() -> None:
    """THE coverage must follow each historical edition rather than a pooled set."""

    frame = _load()
    the = frame.loc[frame["provider"] == "Times Higher Education"].sort_values(
        "admission_year"
    )
    assert [len(_ids(value)) for value in the["verified_parent_ids"]] == [9, 11, 11]
    assert all(_ids(value) == {"uma"} for value in the["unresolved_parent_ids"])

    the_2018 = _ids(the.iloc[0]["verified_parent_ids"])
    assert "utad" not in the_2018
    assert "uevora" not in the_2018

    qs_2020 = frame.loc[
        (frame["provider"] == "QS") & (frame["admission_year"] == 2020),
        "verified_parent_ids",
    ].iloc[0]
    assert len(_ids(the.iloc[2]["verified_parent_ids"])) > len(_ids(qs_2020))
