"""Regression tests for the exact age-18 source registry contract."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_age18_registry_matches_source_locked_release_data() -> None:
    registry = yaml.safe_load((ROOT / "config/source_registry.yml").read_text(encoding="utf-8"))
    exact = registry["sources"]["ine_demography"]["exact_age_18"]
    population = pd.read_csv(
        ROOT / "data/curated/demography/pt_population_age_18_2016_2025.csv",
        dtype={"indicator": str, "age_code": str},
    )

    assert exact["indicator_code"] == "0001223"
    assert exact["source_locked_coverage"] == "2016-2025"
    assert exact["acquisition_status"] == "source_locked"
    assert set(population["indicator"]) == {exact["indicator_code"]}
    assert set(population["geography_code"]) == {"PT"}
    assert set(population["sex_code"]) == {"T"}
    assert set(population["age_code"]) == {"224"}
    assert population["population_year"].tolist() == list(range(2016, 2026))
