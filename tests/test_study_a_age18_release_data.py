"""Release-data regression for the exact age-18 Study A outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from pt_he_pipeline.study_a_age18 import (
    build_age18_endpoint_comparison,
    build_age18_normalised_components,
    build_age18_normalised_stem,
)

ROOT = Path(__file__).resolve().parents[1]


def test_committed_age18_outputs_rebuild_from_source_locked_inputs() -> None:
    population = pd.read_csv(
        ROOT / "data/curated/demography/pt_population_age_18_2016_2025.csv",
        dtype={"indicator": str, "age_code": str},
    )
    stem = pd.read_csv(ROOT / "results/study_a/medium_run_stem_summary.csv")
    components = pd.read_csv(
        ROOT / "results/study_a/medium_run_component_metrics.csv",
        dtype={"stem_code": str},
    )

    rebuilt_stem = build_age18_normalised_stem(stem, population)
    rebuilt_components = build_age18_normalised_components(components, population)
    rebuilt_endpoints = build_age18_endpoint_comparison(rebuilt_components, rebuilt_stem)

    committed_stem = pd.read_csv(ROOT / "results/study_a/age18_stem_metrics.csv")
    committed_components = pd.read_csv(
        ROOT / "results/study_a/age18_component_metrics.csv",
        dtype={"stem_code": str},
    )
    committed_endpoints = pd.read_csv(
        ROOT / "results/study_a/age18_endpoint_comparison.csv",
        dtype={"stem_code": str},
    )

    assert_frame_equal(rebuilt_stem, committed_stem, check_exact=False, rtol=1e-9, atol=1e-9)
    assert_frame_equal(
        rebuilt_components,
        committed_components,
        check_exact=False,
        rtol=1e-9,
        atol=1e-9,
    )
    assert_frame_equal(
        rebuilt_endpoints,
        committed_endpoints,
        check_exact=False,
        rtol=1e-9,
        atol=1e-9,
    )
