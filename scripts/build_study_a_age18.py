"""Build the exact age-18 Study A demographic normalisation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pt_he_pipeline.study_a_age18 import (
    build_age18_endpoint_comparison,
    build_age18_normalised_components,
    build_age18_normalised_stem,
)

ROOT = Path(__file__).resolve().parents[1]
POPULATION_INPUT = ROOT / "data/curated/demography/pt_population_age_18_2016_2025.csv"
STEM_INPUT = ROOT / "results/study_a/medium_run_stem_summary.csv"
COMPONENT_INPUT = ROOT / "results/study_a/medium_run_component_metrics.csv"
OUTPUT_DIR = ROOT / "results/study_a"


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")


def main() -> None:
    population = pd.read_csv(POPULATION_INPUT, dtype={"indicator": str, "age_code": str})
    stem = pd.read_csv(STEM_INPUT)
    components = pd.read_csv(COMPONENT_INPUT, dtype={"stem_code": str})

    normalised_stem = build_age18_normalised_stem(stem, population)
    normalised_components = build_age18_normalised_components(components, population)
    endpoints = build_age18_endpoint_comparison(normalised_components, normalised_stem)

    _write_csv(normalised_stem, OUTPUT_DIR / "age18_stem_metrics.csv")
    _write_csv(normalised_components, OUTPUT_DIR / "age18_component_metrics.csv")
    _write_csv(endpoints, OUTPUT_DIR / "age18_endpoint_comparison.csv")

    all_stem = endpoints.set_index("stem_code").loc["STEM"]
    print("Built exact age-18 Study A demographic normalisation")
    print(f"Raw endpoint change: {100.0 * float(all_stem['raw_placement_change']):+.2f}%")
    print(f"Age-18-normalised endpoint change: {100.0 * float(all_stem['age18_rate_change']):+.2f}%")


if __name__ == "__main__":
    main()
