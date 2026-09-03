"""Study A helpers for DGES broad-area first-phase access statistics.

The official DGES first-phase result notes report one row per broad study area.
This module keeps those published categories intact, validates them against the
national totals, and only then aggregates the registered STEM components.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from pt_he_pipeline.validation import require_columns

AREA_PANEL_REQUIRED_COLUMNS = (
    "year",
    "area",
    "vacancies",
    "first_choice_applicants",
    "placements",
    "remaining_vacancies",
    "source_document",
    "source_table",
)

NATIONAL_PANEL_REQUIRED_COLUMNS = (
    "year",
    "vacancies",
    "candidates",
    "placements",
)

STEM_COMPONENT_LABELS: Mapping[str, str] = {
    "05": "Natural sciences, mathematics and statistics",
    "06": "Information and communication technologies",
    "07": "Engineering, manufacturing and construction",
}

# The source notes use broad Portuguese CNAEF-style area labels.  The mapping
# below is deterministic at that broad level and mirrors the registered
# ISCED-F 2013 broad groups used by the project.
STEM_SOURCE_AREAS: Mapping[str, str] = {
    "Ciências da Vida": "05",
    "Ciências Físicas": "05",
    "Matemática e Estatística": "05",
    "Informática": "06",
    "Engenharia e Técnicas Afins": "07",
    "Indústrias Transformadoras": "07",
    "Arquitetura e Construção": "07",
}

_AREA_ALIASES: Mapping[str, str] = {
    "Arquitectura e Construção": "Arquitetura e Construção",
    "Protecção do Ambiente": "Proteção do Ambiente",
}

ALLOWED_AREA_SOURCE_TABLES = frozenset({"Quadro V", "Quadro XII"})

_COUNT_COLUMNS = (
    "vacancies",
    "first_choice_applicants",
    "placements",
    "remaining_vacancies",
)


def canonicalise_source_area(area: str) -> str:
    """Return a stable source-area label without changing its substantive meaning."""

    value = str(area).strip()
    return _AREA_ALIASES.get(value, value)


def validate_study_a_area_panel(
    area_frame: pd.DataFrame,
    national_frame: pd.DataFrame,
) -> None:
    """Validate the curated broad-area panel against official national totals.

    The compact DGES table contains first-choice applicants, not all programme
    applications.  At the national level each valid candidate contributes one
    first choice, so the area-table sum must equal the national candidate count.
    """

    require_columns(area_frame, AREA_PANEL_REQUIRED_COLUMNS)
    require_columns(national_frame, NATIONAL_PANEL_REQUIRED_COLUMNS)
    if area_frame.empty:
        raise ValueError("Study A area panel must not be empty")
    if national_frame.empty:
        raise ValueError("national first-phase panel must not be empty")

    area = area_frame.copy()
    area["year"] = pd.to_numeric(area["year"], errors="raise").astype(int)
    area["canonical_area"] = area["area"].map(canonicalise_source_area)

    if area.duplicated(["year", "canonical_area"]).any():
        raise ValueError("Study A area panel contains duplicate year/area keys")

    for column in _COUNT_COLUMNS:
        numeric = pd.to_numeric(area[column], errors="coerce")
        if numeric.isna().any():
            raise ValueError(f"{column} must be numeric and non-missing")
        if (numeric < 0).any():
            raise ValueError(f"{column} must be non-negative")
        if not np.equal(numeric, np.floor(numeric)).all():
            raise ValueError(f"{column} must contain integer counts")

    years = sorted(area["year"].unique())
    if not years:
        raise ValueError("Study A area panel contains no valid years")

    reference_areas: set[str] | None = None
    for year in years:
        subset = area.loc[area["year"] == year]
        year_areas = set(subset["canonical_area"].astype(str))
        if reference_areas is None:
            reference_areas = year_areas
        elif year_areas != reference_areas:
            missing = sorted(reference_areas.difference(year_areas))
            added = sorted(year_areas.difference(reference_areas))
            raise ValueError(
                "broad-area coverage changed across years: "
                f"year={year}, missing={missing}, added={added}"
            )

        if subset["source_document"].nunique(dropna=False) != 1:
            raise ValueError(f"year {year} must map to exactly one source document")
        source_tables = set(subset["source_table"].astype(str))
        if not source_tables.issubset(ALLOWED_AREA_SOURCE_TABLES):
            raise ValueError(
                "Study A data must originate from a registered DGES broad-area table: "
                f"year={year}, tables={sorted(source_tables)}"
            )

    national = national_frame.copy()
    national["year"] = pd.to_numeric(national["year"], errors="raise").astype(int)
    if national.duplicated(["year"]).any():
        raise ValueError("national panel contains duplicate years")

    national_by_year = national.set_index("year")
    area_totals = area.groupby("year", as_index=True)[list(_COUNT_COLUMNS)].sum()
    for year in years:
        if year not in national_by_year.index:
            raise ValueError(f"national panel is missing Study A year {year}")
        expected = national_by_year.loc[year]
        observed = area_totals.loc[year]
        comparisons = {
            "vacancies": (observed["vacancies"], expected["vacancies"]),
            "first_choice_applicants": (
                observed["first_choice_applicants"],
                expected["candidates"],
            ),
            "placements": (observed["placements"], expected["placements"]),
        }
        if "remaining_vacancies" in national_by_year.columns:
            comparisons["remaining_vacancies"] = (
                observed["remaining_vacancies"],
                expected["remaining_vacancies"],
            )
        for name, (actual, target) in comparisons.items():
            if int(actual) != int(target):
                raise ValueError(
                    f"DGES area totals do not reconcile for {year} {name}: "
                    f"observed={int(actual)}, expected={int(target)}"
                )


def build_stem_source_area_metrics(
    area_frame: pd.DataFrame,
    national_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return the seven published STEM source areas with transparent metrics."""

    validate_study_a_area_panel(area_frame, national_frame)
    area = area_frame.copy()
    area["canonical_area"] = area["area"].map(canonicalise_source_area)
    area["stem_code"] = area["canonical_area"].map(STEM_SOURCE_AREAS)
    stem = area.loc[area["stem_code"].notna()].copy()
    if stem.empty:
        raise ValueError("no registered STEM source areas were found")

    national = national_frame[["year", "placements"]].rename(
        columns={"placements": "national_placements"}
    )
    stem = stem.merge(national, on="year", how="left", validate="many_to_one")
    stem["stem_component"] = stem["stem_code"].map(STEM_COMPONENT_LABELS)
    stem["placement_share"] = stem["placements"] / stem["national_placements"]
    stem["occupancy_rate"] = stem["placements"] / stem["vacancies"]
    stem["first_choice_pressure"] = stem["first_choice_applicants"] / stem["vacancies"]
    return stem.sort_values(["year", "stem_code", "canonical_area"], kind="stable").reset_index(
        drop=True
    )


def build_stem_component_metrics(
    area_frame: pd.DataFrame,
    national_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate source areas into registered STEM components and add metrics."""

    stem = build_stem_source_area_metrics(area_frame, national_frame)
    grouped = (
        stem.groupby(["year", "stem_code"], as_index=False)[list(_COUNT_COLUMNS)]
        .sum()
        .sort_values(["year", "stem_code"], kind="stable")
        .reset_index(drop=True)
    )
    grouped["stem_component"] = grouped["stem_code"].map(STEM_COMPONENT_LABELS)

    national = national_frame[["year", "placements"]].rename(
        columns={"placements": "national_placements"}
    )
    grouped = grouped.merge(national, on="year", how="left", validate="many_to_one")
    grouped["placement_share"] = grouped["placements"] / grouped["national_placements"]
    grouped["occupancy_rate"] = grouped["placements"] / grouped["vacancies"]
    grouped["first_choice_pressure"] = (
        grouped["first_choice_applicants"] / grouped["vacancies"]
    )
    previous_year = grouped.groupby("stem_code")["year"].shift(1)
    raw_change = grouped.groupby("stem_code")["placements"].pct_change(fill_method=None)
    grouped["placement_yoy_change"] = raw_change.where(grouped["year"] - previous_year == 1)

    start_values = grouped.groupby("stem_code")["placements"].transform("first")
    grouped["placement_change_from_start"] = grouped["placements"] / start_values - 1.0

    ordered_columns = [
        "year",
        "stem_code",
        "stem_component",
        "vacancies",
        "first_choice_applicants",
        "placements",
        "remaining_vacancies",
        "national_placements",
        "placement_share",
        "occupancy_rate",
        "first_choice_pressure",
        "placement_yoy_change",
        "placement_change_from_start",
    ]
    return grouped[ordered_columns]


def build_stem_summary(component_metrics: pd.DataFrame) -> pd.DataFrame:
    """Aggregate all registered STEM components into an all-STEM annual series."""

    required = {
        "year",
        "vacancies",
        "first_choice_applicants",
        "placements",
        "remaining_vacancies",
        "national_placements",
    }
    require_columns(component_metrics, required)
    if component_metrics.empty:
        raise ValueError("component metrics must not be empty")

    aggregate = (
        component_metrics.groupby("year", as_index=False)
        .agg(
            vacancies=("vacancies", "sum"),
            first_choice_applicants=("first_choice_applicants", "sum"),
            placements=("placements", "sum"),
            remaining_vacancies=("remaining_vacancies", "sum"),
            national_placements=("national_placements", "first"),
        )
        .sort_values("year", kind="stable")
        .reset_index(drop=True)
    )
    aggregate["placement_share"] = aggregate["placements"] / aggregate["national_placements"]
    aggregate["occupancy_rate"] = aggregate["placements"] / aggregate["vacancies"]
    aggregate["first_choice_pressure"] = (
        aggregate["first_choice_applicants"] / aggregate["vacancies"]
    )
    previous_year = aggregate["year"].shift(1)
    raw_change = aggregate["placements"].pct_change(fill_method=None)
    aggregate["placement_yoy_change"] = raw_change.where(aggregate["year"] - previous_year == 1)
    aggregate["placement_change_from_start"] = (
        aggregate["placements"] / float(aggregate.iloc[0]["placements"]) - 1.0
    )
    return aggregate


def build_endpoint_comparison(
    component_metrics: pd.DataFrame,
    stem_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Compare the first and last available years without fitting a trend model."""

    if component_metrics.empty or stem_summary.empty:
        raise ValueError("component metrics and STEM summary must not be empty")

    first_year = int(component_metrics["year"].min())
    last_year = int(component_metrics["year"].max())
    if first_year == last_year:
        raise ValueError("endpoint comparison requires at least two years")

    rows: list[dict[str, float | int | str]] = []
    for code in STEM_COMPONENT_LABELS:
        subset = component_metrics.loc[component_metrics["stem_code"] == code].set_index("year")
        if first_year not in subset.index or last_year not in subset.index:
            raise ValueError(f"STEM component {code} is missing an endpoint year")
        start = subset.loc[first_year]
        end = subset.loc[last_year]
        if not isinstance(start, pd.Series) or not isinstance(end, pd.Series):
            raise ValueError(f"STEM component {code} has duplicate endpoint years")
        rows.append(
            _endpoint_row(
                label=STEM_COMPONENT_LABELS[code],
                code=code,
                first_year=first_year,
                last_year=last_year,
                start=start,
                end=end,
            )
        )

    summary = stem_summary.set_index("year")
    summary_start = summary.loc[first_year]
    summary_end = summary.loc[last_year]
    if not isinstance(summary_start, pd.Series) or not isinstance(summary_end, pd.Series):
        raise ValueError("STEM summary has duplicate endpoint years")
    rows.append(
        _endpoint_row(
            label="All registered STEM",
            code="STEM",
            first_year=first_year,
            last_year=last_year,
            start=summary_start,
            end=summary_end,
        )
    )
    return pd.DataFrame(rows)


def _endpoint_row(
    *,
    label: str,
    code: str,
    first_year: int,
    last_year: int,
    start: pd.Series,
    end: pd.Series,
) -> dict[str, float | int | str]:
    """Build one endpoint-comparison record."""

    start_placements = float(start["placements"])
    end_placements = float(end["placements"])
    if start_placements <= 0:
        raise ValueError("endpoint placement count must be positive")

    return {
        "stem_code": code,
        "stem_component": label,
        "first_year": first_year,
        "last_year": last_year,
        "placements_first": int(start_placements),
        "placements_last": int(end_placements),
        "placement_change": end_placements / start_placements - 1.0,
        "placement_share_first": float(start["placement_share"]),
        "placement_share_last": float(end["placement_share"]),
        "placement_share_change_pp": 100.0
        * (float(end["placement_share"]) - float(start["placement_share"])),
        "occupancy_first": float(start["occupancy_rate"]),
        "occupancy_last": float(end["occupancy_rate"]),
        "occupancy_change_pp": 100.0
        * (float(end["occupancy_rate"]) - float(start["occupancy_rate"])),
        "first_choice_pressure_first": float(start["first_choice_pressure"]),
        "first_choice_pressure_last": float(end["first_choice_pressure"]),
    }
