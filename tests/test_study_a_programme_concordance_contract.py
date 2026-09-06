from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "study_a_programme_concordance.yml"
CONCORDANCE = ROOT / "config" / "concordances" / "study_a_programme_fields.csv"


def test_study_a_programme_concordance_policy_freezes_stem_scope() -> None:
    payload = yaml.safe_load(POLICY.read_text(encoding="utf-8"))

    assert payload["study"] == "A"
    assert payload["status"] == "frozen_before_1997_2026_programme_outcome_panel"
    assert payload["primary_stem_definition"]["isced_f_2013_2digit"] == ["05", "06", "07"]
    assert payload["primary_stem_definition"]["report_components_separately"] is True
    assert payload["classification"]["field_membership_is_year_specific"] is True
    assert payload["classification"]["programme_continuity_is_separate"] is True
    assert payload["release_gate"]["continuity_not_required_for_field_aggregation"] is True
    assert payload["interpretation"]["study_b_cross_domain_panel_role"] == (
        "secondary_calibration_not_primary_stem_evidence"
    )


def test_study_a_programme_concordance_schema_is_explicit() -> None:
    frame = pd.read_csv(CONCORDANCE, dtype=str)
    expected = [
        "source_year",
        "source_institution_id",
        "source_course_id",
        "source_course_title",
        "source_degree",
        "isced_f_2013_2digit",
        "classification_basis",
        "classification_source",
        "continuity_id",
        "continuity_status",
        "continuity_source",
        "reviewed_by",
    ]
    assert frame.columns.tolist() == expected
    assert frame.empty
