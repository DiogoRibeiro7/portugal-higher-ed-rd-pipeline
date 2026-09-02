from __future__ import annotations

import pandas as pd
import pytest
from dataexcept import DataValidationError, MissingColumnError

from pt_he_pipeline.ingestion import build_cna_pairs, combined_sha256

SHA_PAIR = "a" * 64
SHA_PLACEMENT = "b" * 64


def _pair() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2025],
            "phase": [1],
            "institution_id": ["0140"],
            "course_id": ["8086"],
            "institution_name": ["Universidade dos Açores"],
            "course_name": ["Medicina Veterinária"],
            "degree": ["PM"],
            "applicants": [120],
            "first_choice_applicants": [30],
            "placements": [22],
            "mean_application_grade_placed": [170.0],
            "last_placed_general_contingent_grade": [166.0],
            "pair_statistics_source_sha256": [SHA_PAIR],
        }
    )


def _placement() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2025],
            "phase": [1],
            "institution_id": ["0140"],
            "course_id": ["8086"],
            "vacancies": [22],
            "placements": [22],
            "last_placed_general_contingent_grade": [166.0],
            "remaining_vacancies": [0],
            "placement_source_sha256": [SHA_PLACEMENT],
        }
    )


def test_combined_sha256_is_order_independent_and_source_binding() -> None:
    first = combined_sha256(SHA_PAIR, SHA_PLACEMENT)
    second = combined_sha256(SHA_PLACEMENT, SHA_PAIR)
    assert first == second
    assert first not in {SHA_PAIR, SHA_PLACEMENT}


def test_build_cna_pairs_checks_and_binds_sources() -> None:
    result = build_cna_pairs(_pair(), _placement())
    assert result.loc[0, "vacancies"] == 22
    assert result.loc[0, "applicants"] == 120
    assert result.loc[0, "source_sha256"] == combined_sha256(SHA_PAIR, SHA_PLACEMENT)


def test_build_cna_pairs_rejects_missing_source_column() -> None:
    pair = _pair().drop(columns=["applicants"])
    with pytest.raises(MissingColumnError, match="applicants"):
        build_cna_pairs(pair, _placement())


def test_build_cna_pairs_rejects_cross_source_placement_mismatch() -> None:
    placement = _placement()
    placement.loc[0, "placements"] = 21
    with pytest.raises(DataValidationError, match="placement count mismatch"):
        build_cna_pairs(_pair(), placement)
