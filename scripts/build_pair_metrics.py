"""Add transparent demand and occupancy metrics to a canonical CNA pair table."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pt_he_pipeline.metrics import add_access_metrics
from pt_he_pipeline.validation import validate_pair_panel


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.casefold() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frame = _read(args.input)
    validate_pair_panel(frame)
    enriched = add_access_metrics(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.casefold() == ".parquet":
        enriched.to_parquet(args.output, index=False)
    else:
        enriched.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
