"""Acquire receipt-locked DGEEC course-classification fichas for a course list."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import requests

from pt_he_pipeline.dgeec_cnaef import fetch_course_ficha


def acquire_course_classifications(
    course_list: pd.DataFrame,
    output_dir: Path,
    *,
    classification_version: int = 2013,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Acquire every unique course classification and retain explicit failures."""

    if "course_id" not in course_list.columns:
        raise ValueError("course_list must contain course_id")
    course_ids = sorted({str(value).strip() for value in course_list["course_id"].dropna()})
    if not course_ids:
        raise ValueError("course_list contains no course ids")

    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for course_id in course_ids:
        destination = output_dir / f"{course_id}_{classification_version}.html"
        try:
            record = fetch_course_ficha(
                course_id,
                destination,
                classification_version=classification_version,
            )
        except (OSError, ValueError, requests.RequestException) as exc:
            failures.append(
                {
                    "course_id": course_id,
                    "classification_version": classification_version,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
            )
            continue
        records.append(record)

    classified = pd.DataFrame(records)
    failed = pd.DataFrame(failures)
    if len(classified) + len(failed) != len(course_ids):
        raise RuntimeError("classification acquisition accounting mismatch")
    return classified, failed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_list", type=Path, help="CSV containing a course_id column")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--classification-version", type=int, choices=(1997, 2013), default=2013)
    args = parser.parse_args()

    frame = pd.read_csv(args.course_list, dtype={"course_id": str})
    try:
        classified, failed = acquire_course_classifications(
            frame,
            args.output_dir,
            classification_version=args.classification_version,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    classified.to_csv(
        args.output_dir / f"dgeec_course_classifications_{args.classification_version}.csv",
        index=False,
    )
    failed.to_csv(
        args.output_dir / f"dgeec_course_classification_failures_{args.classification_version}.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
