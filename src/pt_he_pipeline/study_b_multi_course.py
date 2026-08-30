"""Registered multi-course extension for Study B."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm

from pt_he_pipeline.study_b_course_pilot import MEASURE_COLUMNS, PRIMARY_OUTCOMES
from pt_he_pipeline.validation import require_columns

IDENTIFIERS = ("year", "programme_code", "institution_code")
COUNTS = (
    "vacancies",
    "applicants",
    "first_choice_applicants",
    "placements",
    "first_choice_placements",
)


@dataclass(frozen=True)
class RegisteredProgramme:
    """Exact DGES programme identity."""

    code: str
    name: str
    degree: str = "Licenciatura"


@dataclass(frozen=True)
class MultiCoursePolicy:
    """Coverage rules for the registered panel."""

    first_year: int = 2018
    last_year: int = 2020
    overlap_year: int = 2019
    min_stable_institutions: int = 6

    @property
    def years(self) -> tuple[int, ...]:
        """Return the registered consecutive years."""

        return tuple(range(self.first_year, self.last_year + 1))


def validate_registry(programmes: Sequence[RegisteredProgramme]) -> None:
    """Require non-empty, unique programme identities."""

    if not programmes:
        raise ValueError("programme registry must not be empty")
    codes = [p.code.strip() for p in programmes]
    if any(not code for code in codes) or len(codes) != len(set(codes)):
        raise ValueError("programme codes must be non-empty and unique")
    if any(not p.name.strip() or not p.degree.strip() for p in programmes):
        raise ValueError("programme labels and degrees must not be empty")


def reconcile_sources(
    source: pd.DataFrame,
    *,
    programmes: Sequence[RegisteredProgramme],
    policy: MultiCoursePolicy = MultiCoursePolicy(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate and reconcile duplicated cross-vintage observations."""

    validate_registry(programmes)
    required = (
        "source_document_year",
        "programme_name",
        "degree",
        *IDENTIFIERS,
        *MEASURE_COLUMNS,
    )
    require_columns(source, required)
    frame = _normalise(source)
    registry = {p.code: p for p in programmes}
    if set(frame["programme_code"]) != set(registry):
        raise ValueError("source programmes do not match registry")
    if set(frame["year"]) != set(policy.years):
        raise ValueError("source years do not match policy")

    for code, subset in frame.groupby("programme_code"):
        programme = registry[code]
        if set(subset["programme_name"].astype(str).str.strip()) != {programme.name}:
            raise ValueError(f"programme name mismatch for {code}")
        if set(subset["degree"].astype(str).str.strip()) != {programme.degree}:
            raise ValueError(f"degree mismatch for {code}")
        if set(subset["year"]) != set(policy.years):
            raise ValueError(f"programme {code} does not cover all years")

    for column in COUNTS:
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or (values < 0).any():
            raise ValueError(f"invalid count column: {column}")
    if (frame["vacancies"] <= 0).any():
        raise ValueError("vacancies must be positive")
    if (frame["first_choice_applicants"] > frame["applicants"]).any():
        raise ValueError("first-choice applicants exceed applicants")
    if (frame["first_choice_placements"] > frame["placements"]).any():
        raise ValueError("first-choice placements exceed placements")

    key = ["source_document_year", *IDENTIFIERS]
    if frame.duplicated(key).any():
        raise ValueError("duplicate source-document observation")

    audit_rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(list(IDENTIFIERS), sort=True):
        disagreement = [
            column for column in MEASURE_COLUMNS if group[column].nunique(dropna=False) != 1
        ]
        if disagreement:
            raise ValueError(
                f"overlapping source rows disagree for {keys}: {', '.join(disagreement)}"
            )
        audit_rows.append(
            {
                "year": int(keys[0]),
                "programme_code": str(keys[1]),
                "institution_code": str(keys[2]),
                "source_document_count": int(group["source_document_year"].nunique()),
            }
        )

    canonical = (
        frame.sort_values([*IDENTIFIERS, "source_document_year"], kind="stable")
        .drop_duplicates(list(IDENTIFIERS), keep="last")
        .sort_values(list(IDENTIFIERS), kind="stable")
        .reset_index(drop=True)
    )
    return canonical, pd.DataFrame(audit_rows)


def build_stable_panel(
    canonical: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    programmes: Sequence[RegisteredProgramme],
    policy: MultiCoursePolicy = MultiCoursePolicy(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep units offered in every year using coverage only."""

    require_columns(canonical, (*IDENTIFIERS, "programme_name", *MEASURE_COLUMNS))
    require_columns(audit, (*IDENTIFIERS, "source_document_count"))
    frame = _normalise(canonical)
    audit_frame = _normalise(audit)
    overlap = audit_frame.loc[
        (audit_frame["year"] == policy.overlap_year)
        & (audit_frame["source_document_count"] >= 2)
    ]
    overlap_units = set(zip(overlap.programme_code, overlap.institution_code, strict=False))

    allowed: set[tuple[str, str]] = set()
    coverage: list[dict[str, object]] = []
    for programme in programmes:
        subset = frame.loc[frame["programme_code"] == programme.code]
        observed_any = subset["institution_code"].nunique()
        stable = []
        for institution, rows in subset.groupby("institution_code"):
            unit = (programme.code, str(institution))
            if set(rows["year"]) == set(policy.years) and unit in overlap_units:
                stable.append(str(institution))
                allowed.add(unit)
        coverage.append(
            {
                "programme_code": programme.code,
                "programme_name": programme.name,
                "institutions_observed_any_year": int(observed_any),
                "stable_institutions": len(stable),
            }
        )
        if len(stable) < policy.min_stable_institutions:
            raise ValueError(f"programme {programme.code} fails coverage gate")

    keys = pd.MultiIndex.from_frame(frame[["programme_code", "institution_code"]])
    keep = pd.MultiIndex.from_tuples(sorted(allowed))
    panel = frame.loc[keys.isin(keep)].copy()
    panel = panel.sort_values(list(IDENTIFIERS), kind="stable").reset_index(drop=True)
    return panel, pd.DataFrame(coverage)


def add_metrics(
    panel: pd.DataFrame,
    *,
    policy: MultiCoursePolicy = MultiCoursePolicy(),
) -> pd.DataFrame:
    """Add demand, occupancy and panel identifiers."""

    frame = _normalise(panel)
    vacancies = frame["vacancies"].astype(float)
    frame["applicants_per_vacancy"] = frame["applicants"].astype(float) / vacancies
    frame["first_choice_pressure"] = (
        frame["first_choice_applicants"].astype(float) / vacancies
    )
    frame["occupancy_rate"] = frame["placements"].astype(float) / vacancies
    frame["year_offset"] = frame["year"] - policy.overlap_year
    frame["unit_id"] = frame["programme_code"] + ":" + frame["institution_code"]
    frame["programme_year_id"] = frame["programme_code"] + ":" + frame["year"].astype(str)
    return frame


def build_model_panel(
    panel: pd.DataFrame,
    *,
    policy: MultiCoursePolicy = MultiCoursePolicy(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate complete modelling units from the stable offering panel."""

    rows: list[dict[str, object]] = []
    allowed: set[tuple[str, str]] = set()
    for code, subset in panel.groupby("programme_code"):
        stable = subset["institution_code"].nunique()
        complete = 0
        for institution, unit in subset.groupby("institution_code"):
            ok = (
                set(unit["year"]) == set(policy.years)
                and (unit["applicants_per_vacancy"] > 0).all()
                and unit[list(PRIMARY_OUTCOMES)].notna().all().all()
            )
            if ok:
                complete += 1
                allowed.add((str(code), str(institution)))
        rows.append(
            {
                "programme_code": str(code),
                "stable_institutions": int(stable),
                "model_complete_institutions": complete,
                "excluded_institutions": int(stable - complete),
            }
        )
    keys = pd.MultiIndex.from_frame(panel[["programme_code", "institution_code"]])
    keep = pd.MultiIndex.from_tuples(sorted(allowed))
    model = panel.loc[keys.isin(keep)].copy().reset_index(drop=True)
    return model, pd.DataFrame(rows)


def programme_year_associations(panel: pd.DataFrame) -> pd.DataFrame:
    """Fit one log-demand model inside each programme-year cell."""

    rows: list[dict[str, object]] = []
    for (code, year), subset in panel.groupby(["programme_code", "year"], sort=True):
        if len(subset) < 3 or (subset["applicants_per_vacancy"] <= 0).any():
            raise ValueError("programme-year cell is not model-ready")
        x = sm.add_constant(
            pd.DataFrame({"log_demand": np.log(subset["applicants_per_vacancy"])}),
            has_constant="add",
        )
        for outcome in PRIMARY_OUTCOMES:
            fitted = sm.OLS(subset[outcome].astype(float), x).fit()
            rows.append(
                {
                    "programme_code": str(code),
                    "year": int(year),
                    "outcome": outcome,
                    "n": int(len(subset)),
                    "r_squared": float(fitted.rsquared),
                    "log_demand_coefficient": float(fitted.params["log_demand"]),
                }
            )
    return pd.DataFrame(rows)


def summarise_associations(associations: pd.DataFrame) -> pd.DataFrame:
    """Summarise variation in demand explanatory power across cells."""

    rows = []
    for outcome, subset in associations.groupby("outcome", sort=True):
        values = subset["r_squared"].astype(float)
        rows.append(
            {
                "outcome": outcome,
                "programme_year_cells": int(len(values)),
                "median_r_squared": float(values.median()),
                "q25_r_squared": float(values.quantile(0.25)),
                "q75_r_squared": float(values.quantile(0.75)),
                "share_r_squared_ge_0_50": float((values >= 0.50).mean()),
                "share_r_squared_ge_0_80": float((values >= 0.80).mean()),
            }
        )
    return pd.DataFrame(rows)


def _normalise(frame: pd.DataFrame) -> pd.DataFrame:
    normalised = frame.copy()
    normalised["year"] = pd.to_numeric(normalised["year"], errors="raise").astype(int)
    if "source_document_year" in normalised:
        normalised["source_document_year"] = pd.to_numeric(
            normalised["source_document_year"], errors="raise"
        ).astype(int)
    normalised["programme_code"] = normalised["programme_code"].astype(str).str.strip()
    normalised["institution_code"] = (
        normalised["institution_code"].astype(str).str.strip().str.zfill(4)
    )
    return normalised
