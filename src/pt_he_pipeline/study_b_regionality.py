"""Regionality metrics for Study B.

The module keeps published origin and destination geography intact. The primary
district-diagonal estimand uses only cells whose origin and destination are both
explicitly classified as districts. Autonomous regions and legacy access areas remain
in the full flow table and contribute to the coverage denominator.
"""
from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd

from pt_he_pipeline.validation import require_columns

FLOW_TYPES: Final[tuple[str, ...]] = ("first_choice", "placement")
AREA_TYPES: Final[tuple[str, ...]] = (
    "district",
    "autonomous_region",
    "access_area",
)
REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "source_document_year",
    "year",
    "flow_type",
    "origin_area",
    "origin_area_type",
    "destination_area",
    "destination_area_type",
    "count",
)
CELL_KEY: Final[tuple[str, ...]] = (
    "year",
    "flow_type",
    "origin_area",
    "origin_area_type",
    "destination_area",
    "destination_area_type",
)


def validate_source_flows(source: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalise one or more comparative mobility source tables."""

    require_columns(source, REQUIRED_COLUMNS)
    if source.empty:
        raise ValueError("mobility source table must not be empty")

    frame = source.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["source_document_year"] = pd.to_numeric(
        frame["source_document_year"], errors="raise"
    ).astype(int)
    frame["count"] = pd.to_numeric(frame["count"], errors="raise")
    if (frame["count"] < 0).any() or not np.equal(
        frame["count"], np.floor(frame["count"])
    ).all():
        raise ValueError("mobility counts must be non-negative integers")
    frame["count"] = frame["count"].astype(int)

    if not set(frame["flow_type"]).issubset(FLOW_TYPES):
        raise ValueError("unexpected mobility flow type")
    if not set(frame["origin_area_type"]).issubset(AREA_TYPES):
        raise ValueError("unexpected origin area type")
    if not set(frame["destination_area_type"]).issubset(AREA_TYPES):
        raise ValueError("unexpected destination area type")
    if frame[list(CELL_KEY)].isna().any().any():
        raise ValueError("mobility cell identifiers must not be missing")

    source_key = ["source_document_year", *CELL_KEY]
    if frame.duplicated(source_key).any():
        raise ValueError("duplicate source-document mobility cell")

    totals = frame.groupby(["year", "flow_type"])["count"].sum()
    if (totals <= 0).any():
        raise ValueError("each year/flow type must have a positive total")
    return frame


def reconcile_overlapping_flows(
    source: pd.DataFrame,
    *,
    overlap_year: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Require exact equality across duplicated comparative mobility vintages."""

    frame = validate_source_flows(source)
    audit_rows: list[dict[str, object]] = []
    for key, group in frame.groupby(list(CELL_KEY), sort=True):
        if group["count"].nunique(dropna=False) != 1:
            raise ValueError(f"overlapping mobility source rows disagree for {key}")
        audit_rows.append(
            {
                **dict(zip(CELL_KEY, key, strict=True)),
                "source_document_count": int(group["source_document_year"].nunique()),
                "reconciled": True,
            }
        )

    overlap = frame.loc[frame["year"] == overlap_year]
    if overlap.empty:
        raise ValueError("registered overlap year is absent")
    overlap_counts = overlap.groupby(list(CELL_KEY))["source_document_year"].nunique()
    if not (overlap_counts == 2).all():
        raise ValueError("every overlap-year mobility cell must occur in both documents")

    canonical = (
        frame.sort_values([*CELL_KEY, "source_document_year"], kind="stable")
        .drop_duplicates(list(CELL_KEY), keep="last")
        .sort_values(list(CELL_KEY), kind="stable")
        .reset_index(drop=True)
    )
    return canonical, pd.DataFrame(audit_rows)


def build_regionality_summary(flows: pd.DataFrame) -> pd.DataFrame:
    """Compute registered annual regionality summaries by flow type."""

    require_columns(flows, (*CELL_KEY, "count"))
    rows: list[dict[str, object]] = []
    for (year, flow_type), subset in flows.groupby(["year", "flow_type"], sort=True):
        total = float(subset["count"].sum())
        comparable = subset.loc[subset["origin_area_type"] == "district"].copy()
        comparable_total = float(comparable["count"].sum())
        diagonal = comparable.loc[
            (comparable["destination_area_type"] == "district")
            & (
                comparable["origin_area"].astype(str).str.strip()
                == comparable["destination_area"].astype(str).str.strip()
            )
        ]
        diagonal_total = float(diagonal["count"].sum())

        rows.append(
            {
                "year": int(year),
                "flow_type": str(flow_type),
                "total_flows": int(total),
                "comparable_district_origin_flows": int(comparable_total),
                "comparable_origin_coverage": comparable_total / total,
                "same_district_share": diagonal_total / comparable_total,
                "conditional_entropy": _conditional_entropy(comparable),
                "normalised_mutual_information": _normalised_mutual_information(comparable),
            }
        )
    return pd.DataFrame(rows)


def build_first_choice_placement_contrast(summary: pd.DataFrame) -> pd.DataFrame:
    """Compare preference and realised-placement regionality within each year."""

    require_columns(summary, ("year", "flow_type", "same_district_share"))
    pivot = summary.pivot(index="year", columns="flow_type", values="same_district_share")
    missing = set(FLOW_TYPES) - set(pivot.columns)
    if missing:
        raise ValueError(f"summary is missing flow types: {sorted(missing)}")
    result = pivot.reset_index()
    result["placement_minus_first_choice"] = (
        result["placement"] - result["first_choice"]
    )
    return result


def _conditional_entropy(frame: pd.DataFrame) -> float:
    """Return H(destination | origin) in natural-log units."""

    if frame.empty or frame["count"].sum() <= 0:
        raise ValueError("comparable district flow table must not be empty")
    total = float(frame["count"].sum())
    entropy = 0.0
    for _, group in frame.groupby("origin_area", sort=False):
        origin_total = float(group["count"].sum())
        probabilities = group["count"].to_numpy(dtype=float) / origin_total
        positive = probabilities[probabilities > 0]
        entropy += (origin_total / total) * float(-(positive * np.log(positive)).sum())
    return entropy


def _normalised_mutual_information(frame: pd.DataFrame) -> float:
    """Return mutual information normalised by the larger marginal entropy."""

    table = frame.pivot_table(
        index="origin_area",
        columns="destination_area",
        values="count",
        aggfunc="sum",
        fill_value=0,
    ).to_numpy(dtype=float)
    total = table.sum()
    if total <= 0:
        raise ValueError("comparable district flow table must have positive mass")
    joint = table / total
    p_origin = joint.sum(axis=1)
    p_destination = joint.sum(axis=0)
    expected = np.outer(p_origin, p_destination)
    mask = joint > 0
    mutual_information = float((joint[mask] * np.log(joint[mask] / expected[mask])).sum())
    h_origin = float(-(p_origin[p_origin > 0] * np.log(p_origin[p_origin > 0])).sum())
    h_destination = float(
        -(p_destination[p_destination > 0] * np.log(p_destination[p_destination > 0])).sum()
    )
    denominator = max(h_origin, h_destination)
    return mutual_information / denominator if denominator > 0 else 0.0
