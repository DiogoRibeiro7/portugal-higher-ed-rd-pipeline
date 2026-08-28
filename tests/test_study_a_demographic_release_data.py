"""Contract tests for the v0.3.2 demographic sensitivity release data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pt_he_pipeline.study_a_demography import (
    build_demographic_endpoint_comparison,
    build_demographic_normalised_components,
    build_demographic_normalised_stem,
)

ROOT = Path(__file__).resolve().parents[1]


def test_demographic_release_has_complete_previous_year_denominators() -> None:
    population = pd.read_csv(
        ROOT / "data/curated/demography/pt_population_15_24_2016_2025.csv"
    )
    assert population["population_year"].tolist() == list(range(2016, 2026))
    assert population["population_15_24"].tolist() == [
        1_101_839,
        1_095_605,
        1_091_846,
        1_090_568,
        1_091_205,
        1_102_644,
        1_137_135,
        1_175_671,
        1_192_483,
        1_185_234,
    ]


def test_release_endpoint_normalisation_changes_interpretation_margin() -> None:
    population = pd.read_csv(
        ROOT / "data/curated/demography/pt_population_15_24_2016_2025.csv"
    )
    summary = pd.read_csv(ROOT / "results/study_a/medium_run_stem_summary.csv")
    components = pd.read_csv(ROOT / "results/study_a/medium_run_component_metrics.csv")

    normalised_stem = build_demographic_normalised_stem(summary, population)
    normalised_components = build_demographic_normalised_components(components, population)
    endpoint = build_demographic_endpoint_comparison(
        normalised_components, normalised_stem
    ).set_index("stem_code")

    all_stem = endpoint.loc["STEM"]
    assert all_stem["raw_placement_change"] == pytest.approx(0.09011920149360897)
    assert all_stem["cohort_proxy_rate_change"] == pytest.approx(0.0134166340608832)
    assert all_stem["cohort_proxy_rate_first"] == pytest.approx(126.3887010716)
    assert all_stem["cohort_proxy_rate_last"] == pytest.approx(128.0844120233)

    assert endpoint.loc["05", "cohort_proxy_rate_change"] == pytest.approx(
        -0.133458157599563
    )
    assert endpoint.loc["06", "cohort_proxy_rate_change"] == pytest.approx(
        0.48742138683163
    )
    assert endpoint.loc["07", "cohort_proxy_rate_change"] == pytest.approx(
        0.031908593985991
    )
