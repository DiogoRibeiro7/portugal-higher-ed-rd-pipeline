"""Build the registered Study B regionality evidence from curated DGES matrices."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from pt_he_pipeline.study_b_regionality import (
    build_first_choice_placement_contrast,
    build_regionality_summary,
    reconcile_overlapping_flows,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "curated" / "dges" / "study_b_regionality_matrices.json"
RESULTS = ROOT / "results" / "study_b"


def _load_source(path: Path = SOURCE) -> pd.DataFrame:
    """Validate published row/column totals and return the long source table."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    destinations = payload["destinations"]
    rows: list[dict[str, object]] = []

    for matrix in payload["matrices"]:
        column_totals = [0] * len(destinations)
        matrix_total = 0
        for origin in matrix["origins"]:
            counts = [int(value) for value in origin["counts"]]
            if len(counts) != len(destinations):
                raise ValueError("mobility matrix row has the wrong destination count")
            if sum(counts) != int(origin["published_total"]):
                raise ValueError("mobility matrix row does not match its published total")
            matrix_total += sum(counts)
            column_totals = [left + right for left, right in zip(column_totals, counts, strict=True)]
            for destination, count in zip(destinations, counts, strict=True):
                rows.append(
                    {
                        "source_document_year": int(matrix["source_document_year"]),
                        "source_url": matrix["source_url"],
                        "source_page": int(matrix["source_page"]),
                        "provider_bytes_bundled": bool(matrix["provider_bytes_bundled"]),
                        "year": int(matrix["year"]),
                        "flow_type": matrix["flow_type"],
                        "origin_area": origin["name"],
                        "origin_area_type": origin["area_type"],
                        "destination_area": destination["name"],
                        "destination_area_type": destination["area_type"],
                        "count": int(count),
                    }
                )

        if column_totals != [int(value) for value in matrix["published_destination_totals"]]:
            raise ValueError("mobility matrix columns do not match published totals")
        if matrix_total != int(matrix["published_matrix_total"]):
            raise ValueError("mobility matrix does not match its published grand total")

    return pd.DataFrame(rows)


def build() -> None:
    """Reconcile the 2024 overlap and write the registered regionality outputs."""

    source = _load_source()
    canonical, audit = reconcile_overlapping_flows(source, overlap_year=2024)
    summary = build_regionality_summary(canonical)
    contrast = build_first_choice_placement_contrast(summary)

    RESULTS.mkdir(parents=True, exist_ok=True)
    outputs = {
        "regionality_reconciliation.csv": audit,
        "regionality_flows.csv": canonical,
        "regionality_summary.csv": summary,
        "regionality_first_choice_placement_contrast.csv": contrast,
    }
    for name, frame in outputs.items():
        frame.to_csv(RESULTS / name, index=False)


if __name__ == "__main__":
    build()
