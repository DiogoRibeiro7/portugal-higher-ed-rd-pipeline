"""Audit DGEEC CITE-F coverage of the source-locked 2025 CNA programme universe."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

EXPECTED_PAIR_COUNT = 1132
STEM_GROUPS = {"05", "06", "07"}


def build_coverage(
    pairs: pd.DataFrame,
    courses: pd.DataFrame,
    classified: pd.DataFrame,
    failed: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return course audit, pair audit and summary with complete denominator accounting."""

    required_pairs = {"institution_id", "course_id"}
    required_courses = {"course_id"}
    required_classified = {"course_id", "isced_f_2013_2digit"}
    for frame, required, name in (
        (pairs, required_pairs, "pairs"),
        (courses, required_courses, "courses"),
        (classified, required_classified, "classified"),
    ):
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"{name} missing required columns: {missing}")

    if len(pairs) != EXPECTED_PAIR_COUNT:
        raise ValueError(
            f"2025 CNA pair universe mismatch: expected {EXPECTED_PAIR_COUNT}, got {len(pairs)}"
        )
    if pairs.duplicated(["institution_id", "course_id"]).any():
        raise ValueError("duplicate establishment-course identities in pair universe")
    if courses.duplicated("course_id").any():
        raise ValueError("duplicate course identities in course universe")
    if classified.duplicated("course_id").any():
        raise ValueError("duplicate classified course identities")
    if "course_id" in failed.columns and failed.duplicated("course_id").any():
        raise ValueError("duplicate failed course identities")

    universe = set(courses["course_id"].astype(str))
    classified_ids = set(classified["course_id"].astype(str))
    failed_ids = set(failed["course_id"].astype(str)) if "course_id" in failed.columns else set()
    if classified_ids & failed_ids:
        raise ValueError("course cannot be both classified and failed")
    if classified_ids | failed_ids != universe:
        missing = sorted(universe.difference(classified_ids | failed_ids))
        extra = sorted((classified_ids | failed_ids).difference(universe))
        raise ValueError(f"course accounting mismatch: missing={missing}, extra={extra}")

    class_cols = [
        column
        for column in (
            "course_id",
            "course_name",
            "degree",
            "citef_2013_code",
            "isced_f_2013_2digit",
            "classification_source_url",
            "classification_source_sha256",
        )
        if column in classified.columns
    ]
    course_audit = courses.copy()
    course_audit["course_id"] = course_audit["course_id"].astype(str)
    course_audit = course_audit.merge(
        classified[class_cols],
        on="course_id",
        how="left",
        suffixes=("_cna", "_dgeec"),
    )
    course_audit["classified"] = course_audit["course_id"].isin(classified_ids)
    course_audit["stem_primary"] = course_audit["isced_f_2013_2digit"].isin(STEM_GROUPS)
    if failed_ids:
        failure_cols = [
            column
            for column in ("course_id", "error_type", "error_message")
            if column in failed.columns
        ]
        course_audit = course_audit.merge(failed[failure_cols], on="course_id", how="left")

    pair_audit = pairs.copy()
    pair_audit["course_id"] = pair_audit["course_id"].astype(str)
    pair_audit = pair_audit.merge(
        course_audit[["course_id", "classified", "isced_f_2013_2digit", "stem_primary"]],
        on="course_id",
        how="left",
        validate="many_to_one",
    )
    if pair_audit["classified"].isna().any():
        raise RuntimeError("pair coverage join lost course accounting")

    summary = pd.DataFrame(
        [
            {
                "year": 2025,
                "pair_denominator": len(pair_audit),
                "pair_classified": int(pair_audit["classified"].sum()),
                "pair_classification_coverage": float(pair_audit["classified"].mean()),
                "course_denominator": len(course_audit),
                "course_classified": int(course_audit["classified"].sum()),
                "course_classification_coverage": float(course_audit["classified"].mean()),
                "classified_primary_stem_courses": int(course_audit["stem_primary"].sum()),
                "classified_primary_stem_pairs": int(pair_audit["stem_primary"].sum()),
            }
        ]
    )
    return course_audit, pair_audit, summary


def _read_csv(path: Path, *, dtype: dict[str, str] | None = None) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path, dtype=dtype)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path)
    parser.add_argument("courses", type=Path)
    parser.add_argument("classified", type=Path)
    parser.add_argument("failed", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/study_a/2025_classification"),
    )
    args = parser.parse_args()

    dtype = {"institution_id": str, "course_id": str}
    course_audit, pair_audit, summary = build_coverage(
        _read_csv(args.pairs, dtype=dtype),
        _read_csv(args.courses, dtype={"course_id": str}),
        _read_csv(args.classified, dtype={"course_id": str}),
        _read_csv(args.failed, dtype={"course_id": str}),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    course_audit.to_csv(args.output_dir / "course_classification_audit.csv", index=False)
    pair_audit.to_csv(args.output_dir / "pair_classification_audit.csv", index=False)
    summary.to_csv(args.output_dir / "classification_coverage_summary.csv", index=False)


if __name__ == "__main__":
    main()
