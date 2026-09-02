from __future__ import annotations

import pandas as pd
import pytest
from dataexcept import DataValidationError, MissingColumnError

from pt_he_pipeline.validation import require_columns, validate_mobility_flows, validate_pair_panel

SHA_PAIR = "a" * 64
SHA_PLACEMENT = "b" * 64
SHA_COMBINED = "c" * 64


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "year": [2025],
            "phase": [1],
            "institution_id": ["U001"],
            "course_id": ["C001"],
            "source_institution_id": ["U001"],
            "source_course_id": ["C001"],
            "institution_name": ["Example University"],
            "course_name": ["Example Engineering"],
            "vacancies": [20],
            "applicants": [50],
            "first_choice_applicants": [25],
            "placements": [20],
            "pair_statistics_source_sha256": [SHA_PAIR],
            "placement_source_sha256": [SHA_PLACEMENT],
            "source_sha256": [SHA_COMBINED],
        }
    )


def test_validate_pair_panel_accepts_valid_frame() -> None:
    validate_pair_panel(_valid_frame())


def test_require_columns_raises_structured_missing_column_error() -> None:
    frame = _valid_frame().drop(columns=["placements"])
    with pytest.raises(MissingColumnError, match="placements"):
        require_columns(frame, ["placements"])


def test_validate_pair_panel_rejects_more_placements_than_applicants() -> None:
    frame = _valid_frame()
    frame.loc[0, "placements"] = 60
    with pytest.raises(DataValidationError, match="placements cannot exceed applicants"):
        validate_pair_panel(frame)


def test_validate_pair_panel_rejects_first_choices_above_applicants() -> None:
    frame = _valid_frame()
    frame.loc[0, "first_choice_applicants"] = 60
    with pytest.raises(DataValidationError, match="first_choice_applicants"):
        validate_pair_panel(frame)


def test_validate_pair_panel_rejects_bad_digest() -> None:
    frame = _valid_frame()
    frame.loc[0, "source_sha256"] = "not-a-hash"
    with pytest.raises(DataValidationError, match="source_sha256"):
        validate_pair_panel(frame)


def test_validate_mobility_flows_accepts_access_area_origin() -> None:
    frame = pd.DataFrame(
        {
            "year": [2003],
            "source_document_year": [2004],
            "flow_type": ["first_choice"],
            "origin_area": ["Tâmega"],
            "origin_area_type": ["access_area"],
            "destination_district": ["Porto"],
            "count": [100],
            "source_sha256": [SHA_PAIR],
        }
    )
    validate_mobility_flows(frame)
