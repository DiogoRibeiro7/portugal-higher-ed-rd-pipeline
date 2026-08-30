"""Release-data checks for Study B ranking row-coverage inputs."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "data" / "curated" / "rankings" / "study_b_provider_coverage_status.csv"


def _ids(value: object) -> set[str]:
    """Parse one pipe-separated parent-id field."""
    if pd.isna(value):
        return set()
    text = str(value).strip()
    return {item for item in text.split("|") if item} if text else set()


def test_provider_coverage_has_one_row_per_provider_year() -> None:
    frame = pd.read_csv(STATUS)
    assert len(frame) == 9
    assert not frame.duplicated(["provider", "admission_year"]).any()
    assert set(frame["admission_year"]) == {2018, 2019, 2020}


def test_qs_keeps_registered_six_parent_core() -> None:
    frame = pd.read_csv(STATUS)
    qs = frame.loc[frame["provider"] == "QS"].sort_values("admission_year")
    assert [len(_ids(value)) for value in qs["verified_parent_ids"]] == [6, 6, 6]
    assert all(not _ids(value) for value in qs["unresolved_parent_ids"])


def test_the_resolves_ualg_and_iscte_but_not_madeira() -> None:
    frame = pd.read_csv(STATUS)
    the = frame.loc[frame["provider"] == "Times Higher Education"]
    for row in the.itertuples(index=False):
        verified = _ids(row.verified_parent_ids)
        unresolved = _ids(row.unresolved_parent_ids)
        assert {"ualg", "iscte"}.issubset(verified)
        assert unresolved == {"uma"}


def test_arwu_historical_ranked_parent_counts_are_frozen() -> None:
    frame = pd.read_csv(STATUS)
    arwu = frame.loc[frame["provider"] == "ARWU"].sort_values("admission_year")
    assert [len(_ids(value)) for value in arwu["verified_parent_ids"]] == [5, 4, 6]
    assert all(not _ids(value) for value in arwu["unresolved_parent_ids"])


def test_arwu_candidate_groups_are_not_promoted_to_rank_bands() -> None:
    frame = pd.read_csv(STATUS)
    arwu_2018 = frame.loc[
        (frame["provider"] == "ARWU") & (frame["admission_year"] == 2018)
    ].iloc[0]
    arwu_2019 = frame.loc[
        (frame["provider"] == "ARWU") & (frame["admission_year"] == 2019)
    ].iloc[0]
    assert "nova" not in _ids(arwu_2018["verified_parent_ids"])
    assert "nova" not in _ids(arwu_2019["verified_parent_ids"])
    assert "uc" not in _ids(arwu_2019["verified_parent_ids"])
