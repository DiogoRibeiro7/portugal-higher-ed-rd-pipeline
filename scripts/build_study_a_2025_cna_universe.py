"""Build the source-locked 2025 first-phase CNA pair and course universes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pt_he_pipeline.dges import discover_pair_references_from_html, pair_statistics_index_url
from pt_he_pipeline.io import fetch_with_receipt, sha256_file

EXPECTED_PAIR_COUNT = 1132
YEAR = 2025
PHASE = 1


def build_universe(html_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    html = html_path.read_text(encoding="utf-8", errors="replace")
    source_url = pair_statistics_index_url(YEAR, PHASE)
    references = discover_pair_references_from_html(
        html,
        year=YEAR,
        phase=PHASE,
        base_url=source_url,
    )
    if len(references) != EXPECTED_PAIR_COUNT:
        raise ValueError(
            f"2025 CNA pair universe mismatch: expected {EXPECTED_PAIR_COUNT}, got {len(references)}"
        )

    digest = sha256_file(html_path)
    pairs = pd.DataFrame(
        [
            {
                "year": ref.year,
                "phase": ref.phase,
                "institution_id": ref.institution_id,
                "institution_name": ref.institution_name,
                "course_id": ref.course_id,
                "course_name": ref.course_name,
                "degree": ref.degree,
                "pair_source_url": ref.url,
                "index_source_url": source_url,
                "index_source_sha256": digest,
            }
            for ref in references
        ]
    )
    key = ["institution_id", "course_id"]
    if pairs.duplicated(key).any():
        raise ValueError("duplicate establishment-course identities in 2025 CNA pair universe")

    courses = (
        pairs[["course_id", "course_name", "degree", "index_source_url", "index_source_sha256"]]
        .drop_duplicates("course_id")
        .sort_values("course_id", kind="stable")
        .reset_index(drop=True)
    )
    return pairs.sort_values(key, kind="stable").reset_index(drop=True), courses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("data/curated/dges"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/dges/2025"))
    args = parser.parse_args()

    html_path = args.html
    if html_path is None:
        html_path = args.raw_dir / "col25f1_index.htm"
        fetch_with_receipt(pair_statistics_index_url(YEAR, PHASE), html_path)

    pairs, courses = build_universe(html_path)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(args.output_dir / "study_a_2025_cna_pair_universe.csv", index=False)
    courses.to_csv(args.output_dir / "study_a_2025_cna_course_universe.csv", index=False)


if __name__ == "__main__":
    main()
