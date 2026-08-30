"""Unit tests for the registered Study B regionality layer."""
from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_b_regionality import (
    build_first_choice_placement_contrast,
    build_regionality_summary,
    reconcile_overlapping_flows,
)


def _fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for source_document_year, years in ((2024, (2023, 2024)), (2025, (2024, 2025))):
        for year in years:
            for flow_type in ("first_choice", "placement"):
                for origin, destination, count in (
                    ("Aveiro", "Aveiro", 40),
                    ("Aveiro", "Porto", 10),
                    ("Porto", "Porto", 35),
                    ("Porto", "Aveiro", 15),
                ):
                    rows.append(
                        {
                            "source_document_year": source_document_year,
                            "year": year,
                            "flow_type": flow_type,
                            "origin_area": origin,
                            "origin_area_type": "district",
                            "destination_district": destination,
                            "count": count,
                        }
                    )
                rows.append(
                    {
                        "source_document_year": source_document_year,
                        "year": year,
                        "flow_type": flow_type,
                        "origin_area": "Tâmega",
                        "origin_area_type": "access_area",
                        "destination_district": "Porto",
                        "count": 20,
                    }
                )
    return pd.DataFrame(rows)


def test_reconciliation_requires_exact_overlap() -> None:
    canonical, audit = reconcile_overlapping_flows(_fixture(), overlap_year=2024)
    assert len(canonical) == 30
    overlap = audit.loc[audit["year"] == 2024]
    assert (overlap["source_document_count"] == 2).all()


def test_reconciliation_rejects_changed_overlap_cell() -> None:
    frame = _fixture()
    mask = (
        (frame["source_document_year"] == 2025)
        & (frame["year"] == 2024)
        & (frame["flow_type"] == "first_choice")
        & (frame["origin_area"] == "Aveiro")
        & (frame["destination_district"] == "Aveiro")
    )
    frame.loc[mask, "count"] += 1
    with pytest.raises(ValueError, match="overlapping mobility source rows disagree"):
        reconcile_overlapping_flows(frame, overlap_year=2024)


def test_primary_diagonal_excludes_legacy_access_area() -> None:
    canonical, _ = reconcile_overlapping_flows(_fixture(), overlap_year=2024)
    summary = build_regionality_summary(canonical)
    row = summary.loc[
        (summary["year"] == 2023) & (summary["flow_type"] == "first_choice")
    ].iloc[0]
    assert row["total_flows"] == 120
    assert row["comparable_district_flows"] == 100
    assert row["comparable_origin_coverage"] == pytest.approx(100 / 120)
    assert row["same_district_share"] == pytest.approx(75 / 100)


def test_first_choice_placement_contrast_is_defined_by_year() -> None:
    canonical, _ = reconcile_overlapping_flows(_fixture(), overlap_year=2024)
    summary = build_regionality_summary(canonical)
    contrast = build_first_choice_placement_contrast(summary)
    assert contrast["year"].tolist() == [2023, 2024, 2025]
    assert (contrast["placement_minus_first_choice"] == 0).all()
