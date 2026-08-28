"""Shared typed records used by the project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceReceipt:
    """Provenance record for one immutable downloaded source."""

    url: str
    retrieved_at_utc: str
    size_bytes: int
    sha256: str
    path: Path


@dataclass(frozen=True, slots=True)
class DgesPairReference:
    """Reference to one DGES institution-programme statistics document."""

    year: int
    phase: int
    institution_id: str
    course_id: str
    institution_name: str
    course_name: str
    degree: str | None
    url: str


@dataclass(frozen=True, slots=True)
class DgesPairStatistics:
    """Statistics parsed from one DGES institution-programme detail page."""

    year: int
    phase: int
    institution_id: str
    course_id: str
    institution_name: str
    course_name: str
    degree: str | None
    applicants: int
    first_choice_applicants: int
    placements: int
    mean_application_grade_placed: float | None
    last_placed_general_contingent_grade: float | None


@dataclass(frozen=True, slots=True)
class DgesPlacementRecord:
    """Capacity and cut-off information from a DGES placement table."""

    year: int
    phase: int
    institution_id: str
    course_id: str
    institution_name: str
    course_name: str
    degree: str | None
    vacancies: int
    placements: int
    last_placed_general_contingent_grade: float | None
    remaining_vacancies: int | None


@dataclass(frozen=True, slots=True)
class MobilityFlow:
    """One cell in a DGES access-origin to destination flow matrix."""

    year: int
    source_document_year: int
    flow_type: str
    origin_area: str
    origin_area_type: str
    destination_district: str
    count: int


@dataclass(frozen=True, slots=True)
class RegionalityMetrics:
    """Summary statistics for one origin-destination flow matrix."""

    total_flow: float
    same_district_share: float
    normalised_entropy: float
    mutual_information: float


@dataclass(frozen=True, slots=True)
class TrendSummary:
    """Simple log-linear trend summary."""

    n_years: int
    slope_log_units_per_year: float
    approximate_annual_percent_change: float
    r_squared: float
