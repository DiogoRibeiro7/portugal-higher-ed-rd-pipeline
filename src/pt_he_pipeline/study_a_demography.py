"""Demographic sensitivity helpers for Study A.

The registered Study A asks for an exact age-18 denominator.  Until that
single-age series is source-locked, this module provides a deliberately weaker
cohort-scale sensitivity based on the INE resident population aged 15-24,
disseminated by PORDATA.  Dividing the ten-year band by ten yields an average
single-year cohort size; it is never relabelled as the population aged 18.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from pt_he_pipeline.validation import require_columns

POPULATION_REQUIRED_COLUMNS = (
    "population_year",
    "population_15_24",
    "source_entity",
    "dissemination",
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


@dataclass(frozen=True)
class CohortProxyPolicy:
    """Define the transparent conversion from a broad age band to a cohort proxy."""

    age_band_years: int = 10
    population_lag_years: int = 1

    def validate(self) -> None:
        """Reject policies that would make the denominator uninterpretable."""

        if self.age_band_years <= 0:
            raise ValueError("age_band_years must be positive")
        if self.population_lag_years < 0:
            raise ValueError("population_lag_years must be non-negative")


_DEFAULT_COHORT_PROXY_POLICY = CohortProxyPolicy()


def validate_population_15_24(
    population: pd.DataFrame,
    admission_years: list[int],
    *,
    policy: CohortProxyPolicy = _DEFAULT_COHORT_PROXY_POLICY,
) -> None:
    """Validate demographic coverage required by the admission-year sensitivity."""

    require_columns(population, POPULATION_REQUIRED_COLUMNS)
    policy.validate()
    if population.empty:
        raise ValueError("demographic population frame must not be empty")
    if not admission_years:
        raise ValueError("admission_years must not be empty")

    frame = population.copy()
    frame["population_year"] = pd.to_numeric(
        frame["population_year"], errors="raise"
    ).astype(int)
    if frame["population_year"].duplicated().any():
        raise ValueError("demographic population frame contains duplicate years")

    counts = pd.to_numeric(frame["population_15_24"], errors="coerce")
    if counts.isna().any() or (counts <= 0).any():
        raise ValueError("population_15_24 must contain positive numeric counts")
    if not np.equal(counts, np.floor(counts)).all():
        raise ValueError("population_15_24 must contain integer counts")

    required_years = {
        int(year) - policy.population_lag_years for year in admission_years
    }
    available_years = set(frame["population_year"].astype(int))
    missing = sorted(required_years.difference(available_years))
    if missing:
        raise ValueError(f"demographic population frame is missing years: {missing}")

    if frame["source_entity"].astype(str).str.strip().nunique() != 1:
        raise ValueError("demographic sensitivity must use one source entity")
    if frame["dissemination"].astype(str).str.strip().nunique() != 1:
        raise ValueError("demographic sensitivity must use one dissemination series")


def build_demographic_normalised_stem(
    stem_summary: pd.DataFrame,
    population: pd.DataFrame,
    *,
    policy: CohortProxyPolicy = _DEFAULT_COHORT_PROXY_POLICY,
) -> pd.DataFrame:
    """Attach a broad-cohort denominator to the observed all-STEM series.

    The resulting rate is placements per 1,000 persons in an *average* one-year
    cohort implied by the 15-24 population.  It is not an age-18 rate.
    """

    require_columns(stem_summary, STEM_SUMMARY_REQUIRED_COLUMNS)
    if stem_summary.empty:
        raise ValueError("STEM summary must not be empty")

    summary = stem_summary.copy()
    summary["year"] = pd.to_numeric(summary["year"], errors="raise").astype(int)
    admission_years = sorted(summary["year"].unique().tolist())
    validate_population_15_24(population, admission_years, policy=policy)

    population_frame = population.copy()
    population_frame["population_year"] = pd.to_numeric(
        population_frame["population_year"], errors="raise"
    ).astype(int)
    summary["population_year"] = summary["year"] - policy.population_lag_years
    merged = summary.merge(
        population_frame[["population_year", "population_15_24"]],
        on="population_year",
        how="left",
        validate="one_to_one",
    )
    if merged["population_15_24"].isna().any():
        raise ValueError("demographic merge produced missing population values")

    merged["average_single_year_cohort_proxy"] = (
        merged["population_15_24"].astype(float) / float(policy.age_band_years)
    )
    denominator = merged["average_single_year_cohort_proxy"]
    merged["stem_placements_per_1000_cohort_proxy"] = (
        1000.0 * merged["placements"].astype(float) / denominator
    )
    merged["national_placements_per_1000_cohort_proxy"] = (
        1000.0 * merged["national_placements"].astype(float) / denominator
    )
    return merged.sort_values("year", kind="stable").reset_index(drop=True)


def build_demographic_normalised_components(
    components: pd.DataFrame,
    population: pd.DataFrame,
    *,
    policy: CohortProxyPolicy = _DEFAULT_COHORT_PROXY_POLICY,
) -> pd.DataFrame:
    """Return component-level placement rates using the same cohort proxy."""

    require_columns(components, COMPONENT_REQUIRED_COLUMNS)
    if components.empty:
        raise ValueError("component frame must not be empty")

    frame = components.copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    frame["stem_code"] = frame["stem_code"].astype(str).str.zfill(2)
    admission_years = sorted(frame["year"].unique().tolist())
    validate_population_15_24(population, admission_years, policy=policy)

    pop = population[["population_year", "population_15_24"]].copy()
    pop["population_year"] = pd.to_numeric(
        pop["population_year"], errors="raise"
    ).astype(int)
    frame["population_year"] = frame["year"] - policy.population_lag_years
    merged = frame.merge(
        pop, on="population_year", how="left", validate="many_to_one"
    )
    if merged["population_15_24"].isna().any():
        raise ValueError(
            "component demographic merge produced missing population values"
        )

    merged["average_single_year_cohort_proxy"] = (
        merged["population_15_24"].astype(float) / float(policy.age_band_years)
    )
    merged["placements_per_1000_cohort_proxy"] = (
        1000.0
        * merged["placements"].astype(float)
        / merged["average_single_year_cohort_proxy"]
    )
    return merged.sort_values(["year", "stem_code"], kind="stable").reset_index(drop=True)


def build_demographic_endpoint_comparison(
    normalised_components: pd.DataFrame,
    normalised_stem: pd.DataFrame,
) -> pd.DataFrame:
    """Compare raw and cohort-proxy changes between the observed endpoints."""

    component_required = (
        "year",
        "stem_code",
        "stem_component",
        "placements",
        "placements_per_1000_cohort_proxy",
    )
    stem_required = (
        "year",
        "placements",
        "stem_placements_per_1000_cohort_proxy",
    )
    require_columns(normalised_components, component_required)
    require_columns(normalised_stem, stem_required)

    years = sorted(normalised_stem["year"].astype(int).unique().tolist())
    if len(years) < 2:
        raise ValueError(
            "at least two observed years are required for endpoint comparison"
        )
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
                rate_first=float(start["placements_per_1000_cohort_proxy"]),
                rate_last=float(end["placements_per_1000_cohort_proxy"]),
            )
        )

    stem_indexed = normalised_stem.set_index("year")
    start_stem = stem_indexed.loc[first_year]
    end_stem = stem_indexed.loc[last_year]
    rows.append(
        _endpoint_record(
            stem_code="STEM",
            stem_component="All registered STEM",
            first_year=first_year,
            last_year=last_year,
            placements_first=float(start_stem["placements"]),
            placements_last=float(end_stem["placements"]),
            rate_first=float(start_stem["stem_placements_per_1000_cohort_proxy"]),
            rate_last=float(end_stem["stem_placements_per_1000_cohort_proxy"]),
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
    """Create one raw-versus-normalised endpoint row."""

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
        "cohort_proxy_rate_first": rate_first,
        "cohort_proxy_rate_last": rate_last,
        "cohort_proxy_rate_change": rate_last / rate_first - 1.0,
    }
