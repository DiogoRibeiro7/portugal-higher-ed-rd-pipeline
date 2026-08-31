"""Tests for the deterministic Study B ranking-model runner."""
from __future__ import annotations

import pandas as pd
import pytest

from scripts.run_study_b_rankings import analyse_provider


def _supported_provider_frame() -> pd.DataFrame:
    """Return a synthetic provider frame with LOPO support for ranks and bands."""

    rows: list[dict[str, object]] = []
    parent_specs = {
        "u1": {"rank": 100.0, "rank_band": None},
        "u2": {"rank": 200.0, "rank_band": None},
        "u3": {"rank": 300.0, "rank_band": None},
        "u4": {"rank": None, "rank_band": "401-500"},
        "u5": {"rank": None, "rank_band": "401-500"},
        "u6": {"rank": None, "rank_band": "501-600"},
        "u7": {"rank": None, "rank_band": "501-600"},
    }
    for year in (2018, 2019, 2020):
        for programme_index, programme in enumerate(("9081", "9119"), start=1):
            for parent_index, (parent, ranking) in enumerate(parent_specs.items(), start=1):
                demand = 1.2 + 0.15 * parent_index + 0.05 * programme_index + 0.02 * (year - 2018)
                rows.append(
                    {
                        "programme_code": programme,
                        "year": year,
                        "parent_institution_id": parent,
                        "applicants_per_vacancy": demand,
                        "rank": ranking["rank"],
                        "rank_band": ranking["rank_band"],
                        "last_placed_general_contingent_grade": (
                            120.0 + 2.5 * parent_index + 1.5 * programme_index + 0.4 * (year - 2018)
                        ),
                        "mean_application_grade_placed": (
                            130.0 + 2.0 * parent_index + 1.0 * programme_index + 0.3 * (year - 2018)
                        ),
                    }
                )
    return pd.DataFrame(rows)


def test_analyse_provider_emits_five_registered_rows() -> None:
    """Each provider must emit two grade pairs plus ranking-to-demand."""

    result = analyse_provider(_supported_provider_frame(), provider="QS")
    assert len(result) == 5
    assert set(result["comparison"]) == {"M0_vs_MR", "MD_vs_MDR", "M0_vs_MR_demand"}
    assert set(result["outcome"]) == {
        "last_placed_general_contingent_grade",
        "mean_application_grade_placed",
        "applicants_per_vacancy",
    }
    assert (result["supported_rows"] > 0).all()
    assert (result["supported_rows"] <= result["eligible_rows"]).all()
    assert (result["supported_parents"] > 0).all()


def test_analyse_provider_fails_closed_without_supported_lopo_rows() -> None:
    """A provider with unique held-out bands cannot yield a predictive result."""

    frame = _supported_provider_frame().copy()
    band_parents = sorted(frame.loc[frame["rank_band"].notna(), "parent_institution_id"].unique())
    for index, parent in enumerate(band_parents, start=1):
        frame.loc[frame["parent_institution_id"] == parent, "rank_band"] = f"band-{index}"
    exact_parents = sorted(frame.loc[frame["rank"].notna(), "parent_institution_id"].unique())
    keep = exact_parents[:2] + band_parents
    frame = frame.loc[frame["parent_institution_id"].isin(keep)].copy()

    with pytest.raises(ValueError, match="no supported test observations"):
        analyse_provider(frame, provider="QS")
