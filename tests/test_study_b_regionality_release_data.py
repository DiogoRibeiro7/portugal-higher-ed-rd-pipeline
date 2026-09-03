"""Release-data contracts for the Study B regionality evidence layer."""
from __future__ import annotations

import numpy as np

from pt_he_pipeline.study_b_regionality import (
    build_first_choice_placement_contrast,
    build_regionality_summary,
    reconcile_overlapping_flows,
)
from scripts.build_study_b_regionality import _load_source


def _rebuild():
    source = _load_source()
    canonical, audit = reconcile_overlapping_flows(source, overlap_year=2024)
    summary = build_regionality_summary(canonical)
    contrast = build_first_choice_placement_contrast(summary)
    return source, canonical, audit, summary, contrast


def test_mobility_source_totals_and_overlap_reconcile() -> None:
    source, canonical, audit, _, _ = _rebuild()
    assert len(source) == 3200
    assert len(canonical) == 2400
    overlap = audit.loc[audit["year"] == 2024]
    assert len(overlap) == 800
    assert (overlap["source_document_count"] == 2).all()

    totals = canonical.groupby(["year", "flow_type"])["count"].sum().to_dict()
    assert totals == {
        (2023, "first_choice"): 59073,
        (2023, "placement"): 49438,
        (2024, "first_choice"): 58301,
        (2024, "placement"): 49963,
        (2025, "first_choice"): 48718,
        (2025, "placement"): 43899,
    }


def test_registered_regionality_result_is_stable() -> None:
    _, _, _, summary, contrast = _rebuild()
    expected_first_choice = {
        2023: 0.6402835518601429,
        2024: 0.6523723615370738,
        2025: 0.6396776834575775,
    }
    expected_placement = {
        2023: 0.5555413360634758,
        2024: 0.5725516716682869,
        2025: 0.5786508773612044,
    }
    for year, expected in expected_first_choice.items():
        row = summary.loc[
            (summary["year"] == year) & (summary["flow_type"] == "first_choice")
        ].iloc[0]
        assert np.isclose(row["same_district_share"], expected)
        assert row["comparable_origin_coverage"] > 0.94
    for year, expected in expected_placement.items():
        row = summary.loc[
            (summary["year"] == year) & (summary["flow_type"] == "placement")
        ].iloc[0]
        assert np.isclose(row["same_district_share"], expected)
        assert row["comparable_origin_coverage"] > 0.94

    assert (contrast["placement_minus_first_choice"] < 0).all()


def test_placement_is_more_geographically_disperse_than_first_choice() -> None:
    _, _, _, summary, _ = _rebuild()
    for year in (2023, 2024, 2025):
        first = summary.loc[
            (summary["year"] == year) & (summary["flow_type"] == "first_choice")
        ].iloc[0]
        placement = summary.loc[
            (summary["year"] == year) & (summary["flow_type"] == "placement")
        ].iloc[0]
        assert placement["conditional_entropy"] > first["conditional_entropy"]
        assert placement["normalised_mutual_information"] < first["normalised_mutual_information"]
