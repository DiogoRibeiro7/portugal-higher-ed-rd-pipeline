"""Expected DGES source-vintage manifest construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from pt_he_pipeline.dges import annual_statistics_url, pair_statistics_index_url


@dataclass(frozen=True, slots=True)
class DgesVintage:
    """One year in the deterministic DGES acquisition plan."""

    year: int
    annual_index_url: str | None
    pair_index_url: str | None
    acquisition_mode: str
    status: str
    note: str


def build_dges_vintage_manifest(start_year: int = 1997, end_year: int = 2026) -> pd.DataFrame:
    """Build the registered acquisition plan without claiming unverified URLs."""

    if start_year < 1997 or end_year > 2100 or start_year > end_year:
        raise ValueError("requested DGES year range is invalid")

    vintages: list[DgesVintage] = []
    for year in range(start_year, end_year + 1):
        if year <= 2003:
            vintages.append(
                DgesVintage(
                    year=year,
                    annual_index_url=annual_statistics_url(year),
                    pair_index_url=None,
                    acquisition_mode="annual_archive_discovery",
                    status="official_archive_registered",
                    note=(
                        "Official annual statistics exist; detailed statce URL is not "
                        "pre-assumed."
                    ),
                )
            )
        elif year <= 2025:
            vintages.append(
                DgesVintage(
                    year=year,
                    annual_index_url=annual_statistics_url(year),
                    pair_index_url=pair_statistics_index_url(year, 1),
                    acquisition_mode="standard_statcol_statce",
                    status="verified_url_family",
                    note="Use annual index discovery and first-phase pair-statistics index.",
                )
            )
        else:
            vintages.append(
                DgesVintage(
                    year=year,
                    annual_index_url=(
                        "https://www.dges.gov.pt/coloc/2026/index.asp"
                        if year == 2026
                        else None
                    ),
                    pair_index_url=None,
                    acquisition_mode="current_results_adapter",
                    status=(
                        "partial_current_vintage"
                        if year == 2026
                        else "unregistered_future_vintage"
                    ),
                    note=(
                        "First-phase result files are published via the 2026 placements page; "
                        "do not infer the standard annual-statistics structure until it appears."
                        if year == 2026
                        else "Future year; source family must be verified before use."
                    ),
                )
            )

    return pd.DataFrame.from_records(asdict(vintage) for vintage in vintages)
