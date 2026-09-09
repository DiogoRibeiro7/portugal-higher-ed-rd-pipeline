from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "curated" / "dges" / "study_b_multi_course_2021_source_rows.csv"
EXCLUSIONS = ROOT / "data" / "curated" / "dges" / "study_b_2021_code_transition_exclusions.csv"
COVERAGE = (
    ROOT
    / "results"
    / "study_b"
    / "2021_extension"
    / "study_b_2018_2021_coverage_gate.csv"
)

EXPECTED_COUNTS = {"9081": 13, "9119": 23, "9147": 22, "9219": 8, "9500": 21}
EXPECTED_TRANSITIONS = {
    ("9119", "0903", "G005"),
    ("9119", "1000", "G005"),
    ("9219", "0507", "9555"),
    ("9219", "1000", "9555"),
    ("9219", "1109", "9555"),
    ("9219", "1511", "9555"),
}


def test_materialised_2021_source_has_registered_exact_code_counts() -> None:
    frame = pd.read_csv(SOURCE, dtype={"programme_code": str, "institution_code": str})

    assert len(frame) == 87
    assert frame["year"].eq(2021).all()
    assert frame["source_document_year"].eq(2021).all()
    assert not frame.duplicated(["programme_code", "institution_code", "year"]).any()
    assert frame.groupby("programme_code").size().to_dict() == EXPECTED_COUNTS


def test_materialised_2021_source_excludes_code_transitions() -> None:
    frame = pd.read_csv(SOURCE, dtype={"programme_code": str, "institution_code": str})
    exclusions = pd.read_csv(
        EXCLUSIONS,
        dtype={"programme_code": str, "institution_code": str, "prior_programme_code": str},
    )

    observed = {
        (row.programme_code, row.institution_code, row.prior_programme_code)
        for row in exclusions.itertuples(index=False)
    }
    assert observed == EXPECTED_TRANSITIONS
    assert len(exclusions) == 6

    excluded_keys = {(programme, institution) for programme, institution, _ in observed}
    source_keys = set(zip(frame["programme_code"], frame["institution_code"], strict=True))
    assert excluded_keys.isdisjoint(source_keys)


def test_four_year_coverage_gate_is_frozen_and_passes() -> None:
    coverage = pd.read_csv(COVERAGE, dtype={"programme_code": str})

    observed = coverage.set_index("programme_code")["stable_institutions_2018_2021"].to_dict()
    assert observed == EXPECTED_COUNTS
    assert coverage["minimum_required"].eq(6).all()
    assert coverage["gate_passed"].all()
