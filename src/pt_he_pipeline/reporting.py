"""Coverage and missingness reporting for canonical source tables."""

from __future__ import annotations

import pandas as pd
from dataexcept import DataValidationError, MissingColumnError


def pair_coverage_report(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarise row counts and key-field missingness by year and phase."""

    required = {"year", "phase", "institution_id", "course_id"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise MissingColumnError(missing[0], dataframe="coverage_frame")
    if frame.empty:
        raise DataValidationError(
            "coverage_frame",
            None,
            "frame must not be empty",
        )

    monitored = [
        column
        for column in (
            "vacancies",
            "applicants",
            "first_choice_applicants",
            "placements",
            "mean_application_grade_placed",
            "last_placed_general_contingent_grade",
        )
        if column in frame.columns
    ]

    records: list[dict[str, object]] = []
    for (year, phase), group in frame.groupby(["year", "phase"], sort=True, dropna=False):
        record: dict[str, object] = {
            "year": int(year),
            "phase": int(phase),
            "rows": len(group),
            "institutions": int(group["institution_id"].nunique()),
            "courses": int(group["course_id"].nunique()),
        }
        for column in monitored:
            record[f"missing_{column}_share"] = float(group[column].isna().mean())
        records.append(record)
    return pd.DataFrame.from_records(records)
