"""Deterministic concordance helpers for changing DGES identifiers and labels."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd


def concordance_key(value: str) -> str:
    """Create a conservative accent-insensitive label key."""

    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    plain = re.sub(r"[^0-9a-zA-Z]+", " ", plain)
    return " ".join(plain.casefold().split())


def build_concordance_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    """Generate candidate longitudinal matches without auto-merging programmes.

    Exact source-code continuity is flagged first. Exact normalised labels are
    provided as audit candidates only. The function deliberately avoids fuzzy
    automatic merges across Bologna-era restructurings or renamed programmes.
    """

    required = (
        "year",
        "institution_id",
        "course_id",
        "institution_name",
        "course_name",
    )
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"missing concordance columns: {missing}")

    result = frame[list(required)].copy()
    result["institution_label_key"] = result["institution_name"].astype(str).map(concordance_key)
    result["course_label_key"] = result["course_name"].astype(str).map(concordance_key)
    result["source_pair_key"] = (
        result["institution_id"].astype(str).str.upper()
        + "/"
        + result["course_id"].astype(str).str.upper()
    )
    result["exact_label_pair_key"] = (
        result["institution_label_key"] + "::" + result["course_label_key"]
    )
    return result.sort_values(["source_pair_key", "year"]).reset_index(drop=True)
