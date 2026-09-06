"""Acquire receipt-locked DGEEC course-classification fichas for a course list."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pt_he_pipeline.dgeec_cnaef import fetch_course_ficha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("course_list", type=Path, help="CSV containing a course_id column")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--classification-version", type=int, choices=(1997, 2013), default=2013)
    args = parser.parse_args()

    frame = pd.read_csv(args.course_list, dtype={"course_id": str})
    if "course_id" not in frame.columns:
        raise SystemExit("course_list must contain course_id")
    course_ids = sorted({str(value).strip() for value in frame["course_id"].dropna()})
    if not course_ids:
        raise SystemExit("course_list contains no course ids")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for course_id in course_ids:
        destination = args.output_dir / f"{course_id}_{args.classification_version}.html"
        records.append(
            fetch_course_ficha(
                course_id,
                destination,
                classification_version=args.classification_version,
            )
        )

    pd.DataFrame(records).to_csv(
        args.output_dir / f"dgeec_course_classifications_{args.classification_version}.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
