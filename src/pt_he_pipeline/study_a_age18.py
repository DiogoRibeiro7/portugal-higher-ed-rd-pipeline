"""Exact age-18 demographic normalisation for Study A."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pt_he_pipeline.validation import require_columns

POPULATION_REQUIRED_COLUMNS = (
    "population_year",
    "population_age_18",
    "source_entity",
    "dissemination",
    "indicator",
    "geography_code",
    "sex_code",
    "age_code",
    "source_url",
    "source_last_updated",
)

STEM_SUMMARY_REQUIRED_COLUMNS = (
    "year",
    "placements",
    "national_placements",
    "placement_share",
)

COMPONENT_REQUIRED_COLUMNS = (
    "year",
    "stem_code",
    "stem_component",
    "placements",
)

POPULATION_LAG_YEARS = 1
EXPECTED_INDICATOR = "0001223"
EXPECTED_GEOGRAPHY = "PT"
EXPECTED_SEX = "T"
EXPECTED_AGE_CODE = "224"


def validate_population_age18(
    population: pd.DataFrame,
    admission_years: list[int],
) -> None:
    """Validate exact age-18 population coverage and source identity."""

    require_columns(population, POPULATION_REQUIRED_COLUMNS)
    if population.empty:
        raise ValueError("age-18 population frame must not be empty")
    if not admission_years:
        raise ValueError("admission_years must not be empty")

    frame = population.copy()
    frame["population_year"] = pd.to_numeric(
        frame["population_year"], errors="raise"
    ).astype(int)
    if frame["population_year"].duplicated().any():
        raise ValueError("age-18 population frame contains duplicate years")

    counts = pd.to_numeric(frame["population_age_18"], errors="coerce")
    if counts.isna().any() or (counts <= 0).any():
        raise ValueError("population_age_18 must contain positive numeric counts")
    if not np.equal(counts, np.floor(counts)).all():
        raise ValueError("population_age_18 must contain integer counts")

    required_years = {int(year) - POPULATION_LAG_YEARS for year in admission_years}
    available_years = set(frame["population_year"])
    missing = sorted(required_years.difference(available_years))
    if missing:
        raise ValueError(f"age-18 population frame is missing years: {missing}")

    expected = {
        "source_entity": "INE",
        "dissemination": "INE JSON API",
        "indicator": EXPECTED_INDICATOR,
        "geography_code": EXPECTED_GEOGRAPHY,
        "sex_code": EXPECTED_SEX,
        "age_code": EXPECTED_AGE_CODE,
    }
    for column, value in expected.items():
        observed = set(frame[column].astype(str).str.strip())
        if observed != {value}:
            raise ValueError(f"unexpected age-18 source identity in {column}: {sorted(observed)}")


def build_age18_normalised_stem(
    stem_summary: pd.DataFrame,
    population: pd.DataFrame,
) -> pd.DataFrame:
    """Attach exact age-18 denominator to the observed all-STEM series."""

    require_columns(stem_summary, STEM_SUMMARY_REQUIRED_COLUMNS)
    if stem_summary.empty:
        raise ValueError("STEM summary must not be empty")

    summary = stem_summary.copy()
    summary["year"] = pd.to_numeric(summary["year"], errors="raise").astype(int)
    validate_population_age18(population, sorted(summary["year"].unique().tolist()))

    pop = population[["population_year", "population_age_18"]].copy()
    pop["population_year"] = pd.to_numeric(pop["population_year"], errors="raise").astype(int)
    summary["population_year"] = summary["year"] - POPULATION_LAG_YEARS
    merged = summary.merge(pop, on="population_year", how="left", validate="one_to_one")
    if merged["population_age_18"].isna().any():
        raise ValueError("age-18 demographic merge produced missing population values")

    denominator = merged["population_age_18"].astype(float)
    merged["stem_placements_per_1000_age18"] = (
        1000.0 * merged["placements"].astype(float) / denominator
    )
    merged["national_placements_per_1000_age18"] = (
        1000.0 * merged["national_placements"].astype(float) / denominator
    )
    return merged.sort_values("year", kind="stable").reset_index(drop=True)


def build_age18_normalised_components(
    components: pd.DataFrame,
    population: pd.DataFrame,
) -> pd.DataFrame:
    """Return component-level placement rates using exact age-18 population."""

    require_columns(components, COMPONENT_REQUIRED_COLUMNS)
    if components.empty:
        raise ValueError("component frame must not be empty")

    frame = components.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["stem_code"] = frame["stem_code"].astype(str).str.zfill(2)
    validate_population_age18(population, sorted(frame["year"].unique().tolist()))

    pop = population[["population_year", "population_age_18"]].copy()
    pop["population_year"] = pd.to_numeric(pop["population_year"], errors="raise").astype(int)
    frame["population_year"] = frame["year"] - POPULATION_LAG_YEARS
    merged = frame.merge(pop, on="population_year", how="left", validate="many_to_one")
    if merged["population_age_18"].isna().any():
        raise ValueError("component age-18 merge produced missing population values")

    merged["placements_per_1000_age18"] = (
        1000.0 * merged["placements"].astype(float) / merged["population_age_18"].astype(float)
    )
    return merged.sort_values(["year", "stem_code"], kind="stable").reset_index(drop=True)


def build_age18_endpoint_comparison(
    normalised_components: pd.DataFrame,
    normalised_stem: pd.DataFrame,
) -> pd.DataFrame:
    """Compare raw and exact-age-normalised changes at observed endpoints."""

    require_columns(
        normalised_components,
        ("year", "stem_code", "stem_component", "placements", "placements_per_1000_age18"),
    )
    require_columns(
        normalised_stem,
        ("year", "placements", "stem_placements_per_1000_age18"),
    )

    years = sorted(normalised_stem["year"].astype(int).unique().tolist())
    if len(years) < 2:
        raise ValueError("at least two observed years are required for endpoint comparison")
    first_year, last_year = years[0], years[-1]

    rows: list[dict[str, float | int | str]] = []
    for code, subset in normalised_components.groupby("stem_code", sort=True):
        indexed = subset.set_index("year")
        start = indexed.loc[first_year]
        end = indexed.loc[last_year]
        rows.append(
            _endpoint_record(
                stem_code=str(code),
                stem_component=str(start["stem_component"]),
                first_year=first_year,
                last_year=last_year,
                placements_first=float(start["placements"]),
                placements_last=float(end["placements"]),
                rate_first=float(start["placements_per_1000_age18"]),
                rate_last=float(end["placements_per_1000_age18"]),
            )
        )

    stem = normalised_stem.set_index("year")
    rows.append(
        _endpoint_record(
            stem_code="STEM",
            stem_component="All registered STEM",
            first_year=first_year,
            last_year=last_year,
            placements_first=float(stem.loc[first_year, "placements"]),
            placements_last=float(stem.loc[last_year, "placements"]),
            rate_first=float(stem.loc[first_year, "stem_placements_per_1000_age18"]),
            rate_last=float(stem.loc[last_year, "stem_placements_per_1000_age18"]),
        )
    )
    return pd.DataFrame(rows)


def _endpoint_record(
    *,
    stem_code: str,
    stem_component: str,
    first_year: int,
    last_year: int,
    placements_first: float,
    placements_last: float,
    rate_first: float,
    rate_last: float,
) -> dict[str, float | int | str]:
    if placements_first <= 0 or rate_first <= 0:
        raise ValueError("endpoint denominators must be positive")
    return {
        "stem_code": stem_code,
        "stem_component": stem_component,
        "first_year": first_year,
        "last_year": last_year,
        "placements_first": int(placements_first),
        "placements_last": int(placements_last),
        "raw_placement_change": placements_last / placements_first - 1.0,
        "age18_rate_first": rate_first,
        "age18_rate_last": rate_last,
        "age18_rate_change": rate_last / rate_first - 1.0,
    }
