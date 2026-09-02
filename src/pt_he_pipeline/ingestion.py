"""Canonical joins and provenance rules for DGES source tables."""

from __future__ import annotations

import hashlib

import pandas as pd
from dataexcept import DataValidationError, MissingColumnError

from pt_he_pipeline.validation import validate_pair_panel

_PAIR_KEYS = ["year", "phase", "institution_id", "course_id"]


def combined_sha256(*digests: str) -> str:
    """Return a deterministic digest binding all distinct input digests."""

    cleaned = sorted({digest.strip().casefold() for digest in digests if digest.strip()})
    if not cleaned:
        raise ValueError("at least one digest is required")
    for digest in cleaned:
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid SHA-256 digest: {digest!r}")
    payload = "\n".join(cleaned).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def build_cna_pairs(pair_statistics: pd.DataFrame, placements: pd.DataFrame) -> pd.DataFrame:
    """Join DGES pair statistics to vacancy/placement records one-to-one."""

    required_pair = set(_PAIR_KEYS) | {
        "institution_name",
        "course_name",
        "applicants",
        "first_choice_applicants",
        "placements",
        "pair_statistics_source_sha256",
    }
    required_placement = set(_PAIR_KEYS) | {
        "vacancies",
        "placements",
        "placement_source_sha256",
    }
    missing_pair = sorted(required_pair.difference(pair_statistics.columns))
    missing_placement = sorted(required_placement.difference(placements.columns))
    if missing_pair:
        raise MissingColumnError(missing_pair[0], dataframe="pair_statistics")
    if missing_placement:
        raise MissingColumnError(missing_placement[0], dataframe="placements")

    if pair_statistics.duplicated(_PAIR_KEYS).any():
        raise DataValidationError(
            "pair_keys",
            None,
            "pair statistics contain duplicate year/phase/institution/course keys",
        )
    if placements.duplicated(_PAIR_KEYS).any():
        raise DataValidationError(
            "pair_keys",
            None,
            "placement table contains duplicate year/phase/institution/course keys",
        )

    merged = pair_statistics.merge(
        placements,
        on=_PAIR_KEYS,
        how="inner",
        validate="one_to_one",
        suffixes=("_pair", "_placement"),
    )
    if merged.empty:
        raise DataValidationError(
            "pair_keys",
            None,
            "pair statistics and placement tables have no overlapping keys",
        )

    pair_placements = pd.to_numeric(merged["placements_pair"], errors="raise")
    table_placements = pd.to_numeric(merged["placements_placement"], errors="raise")
    mismatch = pair_placements.ne(table_placements)
    if mismatch.any():
        bad = merged.loc[mismatch, [*_PAIR_KEYS, "placements_pair", "placements_placement"]]
        examples = bad.to_dict("records")[:3]
        raise DataValidationError(
            "placements",
            examples,
            f"placement count mismatch across DGES sources: {examples}",
        )

    result = pd.DataFrame({key: merged[key] for key in _PAIR_KEYS})
    result["source_institution_id"] = merged["institution_id"]
    result["source_course_id"] = merged["course_id"]
    institution_name_column = (
        "institution_name_pair" if "institution_name_pair" in merged else "institution_name"
    )
    course_name_column = "course_name_pair" if "course_name_pair" in merged else "course_name"
    degree_column = (
        "degree_pair"
        if "degree_pair" in merged
        else ("degree" if "degree" in merged else None)
    )
    result["institution_name"] = merged[institution_name_column]
    result["course_name"] = merged[course_name_column]
    result["degree"] = (
        merged[degree_column] if degree_column is not None else pd.Series(pd.NA, index=merged.index)
    )
    result["vacancies"] = pd.to_numeric(merged["vacancies"], errors="raise").astype("int64")
    result["applicants"] = pd.to_numeric(merged["applicants"], errors="raise").astype("int64")
    result["first_choice_applicants"] = pd.to_numeric(
        merged["first_choice_applicants"], errors="raise"
    ).astype("int64")
    result["placements"] = pair_placements.astype("int64")

    for column in (
        "mean_application_grade_placed",
        "last_placed_general_contingent_grade",
        "remaining_vacancies",
    ):
        pair_name = f"{column}_pair"
        placement_name = f"{column}_placement"
        if placement_name in merged:
            result[column] = merged[placement_name]
        elif pair_name in merged:
            result[column] = merged[pair_name]
        else:
            result[column] = pd.NA

    result["pair_statistics_source_sha256"] = merged["pair_statistics_source_sha256"]
    result["placement_source_sha256"] = merged["placement_source_sha256"]
    result["source_sha256"] = [
        combined_sha256(pair_digest, placement_digest)
        for pair_digest, placement_digest in zip(
            result["pair_statistics_source_sha256"],
            result["placement_source_sha256"],
            strict=True,
        )
    ]

    result = result.sort_values(_PAIR_KEYS).reset_index(drop=True)
    validate_pair_panel(result)
    return result
