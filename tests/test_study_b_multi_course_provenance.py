"""Provenance regressions for the released Study B multi-course source layer."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CURATED_DIR = ROOT / "data" / "curated" / "dges"
MANIFEST = ROOT / "data" / "source_manifests" / "dges_study_b_multi_course.csv"
REGISTRY = ROOT / "data" / "source_manifests" / "dges_study_b_multi_course_registry.csv"
SOURCE_SHARDS = (
    "course_9081_economics_2018_2020_source_rows.csv",
    "course_9119_engineering_informatics_2018_2020_source_rows.csv",
    "course_9147_management_2018_2020_source_rows_part1.csv",
    "course_9147_management_2018_2020_source_rows_part2a.csv",
    "course_9147_management_2018_2020_source_rows_part2b.csv",
    "course_9219_psychology_2018_2020_source_rows.csv",
    "course_9500_nursing_2018_2020_source_rows_part1.csv",
    "course_9500_nursing_2018_2020_source_rows_part2.csv",
    "course_9500_nursing_2018_2020_source_rows_part3.csv",
    "course_9500_nursing_2018_2020_source_rows_part4.csv",
)


def _pairs(frame: pd.DataFrame) -> set[tuple[str, int]]:
    return {
        (str(row.programme_code), int(row.source_document_year))
        for row in frame.itertuples(index=False)
    }


def test_released_multi_course_shards_match_registered_provenance() -> None:
    paths = [CURATED_DIR / name for name in SOURCE_SHARDS]
    assert all(path.is_file() for path in paths)

    shard_rows = pd.concat(
        [pd.read_csv(path, dtype={"programme_code": str}) for path in paths],
        ignore_index=True,
    )
    manifest = pd.read_csv(MANIFEST, dtype={"programme_code": str})
    registry = pd.read_csv(REGISTRY, dtype={"programme_code": str})

    expected = _pairs(manifest)
    assert expected == _pairs(registry) == _pairs(shard_rows)
    assert len(expected) == 10
    assert set(manifest["curation_status"]) == {"curated_transcription_available"}
    assert set(registry["status"]) == {"curated_transcription_available"}
