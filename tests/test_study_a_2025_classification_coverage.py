import pandas as pd
import pytest

from scripts.build_study_a_2025_classification_coverage import (
    EXPECTED_PAIR_COUNT,
    build_coverage,
)


def _pairs() -> pd.DataFrame:
    rows = []
    for index in range(EXPECTED_PAIR_COUNT):
        rows.append(
            {
                "institution_id": f"{index % 9999:04d}",
                "course_id": "9119" if index < 700 else "9081",
            }
        )
    return pd.DataFrame(rows)


def test_build_coverage_preserves_course_and_pair_denominators() -> None:
    pairs = _pairs()
    courses = pd.DataFrame({"course_id": ["9081", "9119"]})
    classified = pd.DataFrame(
        {
            "course_id": ["9119"],
            "isced_f_2013_2digit": ["06"],
            "citef_2013_code": ["0613"],
        }
    )
    failed = pd.DataFrame(
        {
            "course_id": ["9081"],
            "error_type": ["ValueError"],
            "error_message": ["missing ficha"],
        }
    )

    course_audit, pair_audit, summary = build_coverage(pairs, courses, classified, failed)

    assert len(course_audit) == 2
    assert len(pair_audit) == EXPECTED_PAIR_COUNT
    assert summary.loc[0, "course_denominator"] == 2
    assert summary.loc[0, "course_classified"] == 1
    assert summary.loc[0, "course_classification_coverage"] == pytest.approx(0.5)
    assert summary.loc[0, "pair_denominator"] == EXPECTED_PAIR_COUNT
    assert summary.loc[0, "pair_classified"] == 700
    assert summary.loc[0, "pair_classification_coverage"] == pytest.approx(700 / EXPECTED_PAIR_COUNT)
    assert summary.loc[0, "classified_primary_stem_courses"] == 1
    assert summary.loc[0, "classified_primary_stem_pairs"] == 700


def test_build_coverage_rejects_unaccounted_course() -> None:
    pairs = _pairs()
    courses = pd.DataFrame({"course_id": ["9081", "9119"]})
    classified = pd.DataFrame(
        {"course_id": ["9119"], "isced_f_2013_2digit": ["06"]}
    )
    failed = pd.DataFrame(columns=["course_id"])

    with pytest.raises(ValueError, match="course accounting mismatch"):
        build_coverage(pairs, courses, classified, failed)


def test_build_coverage_rejects_overlap_between_classified_and_failed() -> None:
    pairs = _pairs()
    courses = pd.DataFrame({"course_id": ["9081", "9119"]})
    classified = pd.DataFrame(
        {
            "course_id": ["9081", "9119"],
            "isced_f_2013_2digit": ["03", "06"],
        }
    )
    failed = pd.DataFrame({"course_id": ["9081"]})

    with pytest.raises(ValueError, match="both classified and failed"):
        build_coverage(pairs, courses, classified, failed)
