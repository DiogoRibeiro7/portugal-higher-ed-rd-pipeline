"""Tests for the exact age-18 Study A denominator."""

from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_a_age18 import (
    build_age18_endpoint_comparison,
    build_age18_normalised_components,
    build_age18_normalised_stem,
    validate_population_age18,
)


def _population() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "population_year": [2016, 2017, 2019],
            "population_age_18": [100_000, 110_000, 120_000],
            "source_entity": ["INE"] * 3,
            "dissemination": ["INE JSON API"] * 3,
            "indicator": ["0001223"] * 3,
            "geography_code": ["PT"] * 3,
            "sex_code": ["T"] * 3,
            "age_code": ["224"] * 3,
            "source_url": ["https://example.test"] * 3,
            "source_last_updated": ["2026-06-22"] * 3,
        }
    )


def test_age18_validation_uses_previous_years() -> None:
    validate_population_age18(_population(), [2017, 2018, 2020])


def test_age18_validation_rejects_missing_required_year() -> None:
    with pytest.raises(ValueError, match="missing years"):
        validate_population_age18(_population(), [2017, 2019])


def test_age18_validation_rejects_wrong_source_identity() -> None:
    population = _population()
    population.loc[0, "age_code"] = "999"
    with pytest.raises(ValueError, match="age_code"):
        validate_population_age18(population, [2017])


def test_age18_stem_rate_uses_exact_denominator() -> None:
    summary = pd.DataFrame(
        {
            "year": [2017, 2018, 2020],
            "placements": [10_000, 11_000, 12_000],
            "national_placements": [40_000, 42_000, 44_000],
            "placement_share": [0.25, 11_000 / 42_000, 12_000 / 44_000],
        }
    )
    result = build_age18_normalised_stem(summary, _population())
    assert result.loc[0, "population_year"] == 2016
    assert result.loc[0, "population_age_18"] == 100_000
    assert result.loc[0, "stem_placements_per_1000_age18"] == 100.0


def test_age18_endpoint_comparison_separates_raw_and_normalised_change() -> None:
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
    normalised_components = build_age18_normalised_components(components, population)
    normalised_stem = build_age18_normalised_stem(summary, population)
    result = build_age18_endpoint_comparison(normalised_components, normalised_stem)
    science = result.set_index("stem_code").loc["05"]
    assert science["raw_placement_change"] == pytest.approx(0.2)
    assert science["age18_rate_change"] == pytest.approx(0.0)
