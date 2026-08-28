"""Tests for the Study A broad-cohort demographic sensitivity."""

from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_a_demography import (
    CohortProxyPolicy,
    build_demographic_endpoint_comparison,
    build_demographic_normalised_components,
    build_demographic_normalised_stem,
    validate_population_15_24,
)


def _population() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "population_year": [2016, 2017, 2019],
            "population_15_24": [1_000_000, 1_100_000, 1_200_000],
            "source_entity": ["INE"] * 3,
            "dissemination": ["PORDATA"] * 3,
            "source_url": ["https://example.test"] * 3,
            "source_last_updated": ["2026-06-22"] * 3,
        }
    )


def test_population_validation_uses_previous_years() -> None:
    validate_population_15_24(_population(), [2017, 2018, 2020])


def test_population_validation_rejects_missing_required_year() -> None:
    with pytest.raises(ValueError, match="missing years"):
        validate_population_15_24(_population(), [2017, 2019])


def test_policy_rejects_non_positive_age_band() -> None:
    with pytest.raises(ValueError, match="age_band_years"):
        CohortProxyPolicy(age_band_years=0).validate()


def test_stem_rate_is_explicit_average_cohort_proxy() -> None:
    summary = pd.DataFrame(
        {
            "year": [2017, 2018, 2020],
            "placements": [10_000, 11_000, 12_000],
            "national_placements": [40_000, 42_000, 44_000],
            "placement_share": [0.25, 11_000 / 42_000, 12_000 / 44_000],
        }
    )
    result = build_demographic_normalised_stem(summary, _population())
    assert result.loc[0, "population_year"] == 2016
    assert result.loc[0, "average_single_year_cohort_proxy"] == 100_000
    assert result.loc[0, "stem_placements_per_1000_cohort_proxy"] == 100.0


def test_component_endpoint_comparison_separates_raw_and_normalised_change() -> None:
    components = pd.DataFrame(
        {
            "year": [2017, 2020],
            "stem_code": ["05", "05"],
            "stem_component": ["Science", "Science"],
            "placements": [10_000, 12_000],
        }
    )
    summary = pd.DataFrame(
        {
            "year": [2017, 2020],
            "placements": [10_000, 12_000],
            "national_placements": [40_000, 44_000],
            "placement_share": [0.25, 12_000 / 44_000],
        }
    )
    population = _population().loc[_population()["population_year"].isin([2016, 2019])]
    normalised_components = build_demographic_normalised_components(components, population)
    normalised_stem = build_demographic_normalised_stem(summary, population)
    result = build_demographic_endpoint_comparison(normalised_components, normalised_stem)
    science = result.set_index("stem_code").loc["05"]
    assert science["raw_placement_change"] == pytest.approx(0.2)
    assert science["cohort_proxy_rate_change"] == pytest.approx(0.0)
