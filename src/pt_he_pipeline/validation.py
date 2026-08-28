"""Validation for canonical analysis tables."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

PAIR_REQUIRED_COLUMNS = (
    "year",
    "phase",
    "institution_id",
    "course_id",
    "source_institution_id",
    "source_course_id",
    "institution_name",
    "course_name",
    "vacancies",
    "applicants",
    "first_choice_applicants",
    "placements",
    "pair_statistics_source_sha256",
    "placement_source_sha256",
    "source_sha256",
)

MOBILITY_REQUIRED_COLUMNS = (
    "year",
    "source_document_year",
    "flow_type",
    "origin_area",
    "origin_area_type",
    "destination_district",
    "count",
    "source_sha256",
)


def require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    """Raise ``ValueError`` when required columns are absent."""

    required = tuple(columns)
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {missing}")


def _validate_sha256_column(frame: pd.DataFrame, column: str) -> None:
    values = frame[column].astype(str)
    if values.str.fullmatch(r"[0-9a-f]{64}").eq(False).any():
        raise ValueError(f"{column} must contain lowercase 64-character SHA-256 digests")


def validate_pair_panel(frame: pd.DataFrame) -> None:
    """Validate the invariants of the canonical CNA pair panel."""

    require_columns(frame, PAIR_REQUIRED_COLUMNS)
    if frame.empty:
        raise ValueError("pair panel must not be empty")

    if frame[["year", "phase", "institution_id", "course_id"]].isna().any().any():
        raise ValueError("year, phase, institution_id and course_id must not be missing")

    years = pd.to_numeric(frame["year"], errors="coerce")
    phases = pd.to_numeric(frame["phase"], errors="coerce")
    if years.isna().any() or (years < 1997).any() or (years > 2100).any():
        raise ValueError("year must be numeric and within the registered study range")
    if phases.isna().any() or ~phases.isin([1, 2, 3]).all():
        raise ValueError("phase must be one of 1, 2 or 3")

    pair_keys = ["year", "phase", "institution_id", "course_id"]
    if frame.duplicated(pair_keys).any():
        raise ValueError(
            "canonical pair panel contains duplicate year/phase/institution/course keys"
        )

    for column in ("vacancies", "applicants", "first_choice_applicants", "placements"):
        numeric = pd.to_numeric(frame[column], errors="coerce")
        if numeric.isna().any():
            raise ValueError(f"{column} must be numeric and non-missing")
        if (numeric < 0).any():
            raise ValueError(f"{column} must be non-negative")

    applicants = pd.to_numeric(frame["applicants"], errors="raise")
    first_choice = pd.to_numeric(frame["first_choice_applicants"], errors="raise")
    placements = pd.to_numeric(frame["placements"], errors="raise")
    if (first_choice > applicants).any():
        raise ValueError("first_choice_applicants cannot exceed applicants")
    if (placements > applicants).any():
        raise ValueError("placements cannot exceed applicants")

    for column in (
        "pair_statistics_source_sha256",
        "placement_source_sha256",
        "source_sha256",
    ):
        _validate_sha256_column(frame, column)


def validate_mobility_flows(frame: pd.DataFrame) -> None:
    """Validate the long-form DGES mobility-flow contract."""

    require_columns(frame, MOBILITY_REQUIRED_COLUMNS)
    if frame.empty:
        raise ValueError("mobility flow table must not be empty")
    if ~frame["flow_type"].isin(["first_choice", "placement"]).all():
        raise ValueError("flow_type must be first_choice or placement")
    if ~frame["origin_area_type"].isin(["district", "autonomous_region", "access_area"]).all():
        raise ValueError("origin_area_type contains an unregistered category")
    counts = pd.to_numeric(frame["count"], errors="coerce")
    if counts.isna().any() or (counts < 0).any():
        raise ValueError("mobility counts must be numeric and non-negative")
    _validate_sha256_column(frame, "source_sha256")
