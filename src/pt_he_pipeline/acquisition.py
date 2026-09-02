"""Receipt-bound acquisition workflows for standard DGES annual vintages."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from dataexcept import DataValidationError, MissingDataError

from pt_he_pipeline.dges import discover_documents
from pt_he_pipeline.io import fetch_with_receipt

STANDARD_REQUIRED_DOCUMENTS: tuple[str, ...] = (
    "pair_statistics_all",
    "last_placed_grades",
    "mobility",
)


def _safe_remote_filename(url: str, *, fallback: str) -> str:
    """Extract a filename from an official URL without accepting path traversal."""

    name = Path(urlparse(url).path).name
    if not name:
        name = fallback
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise DataValidationError(
            "source_filename",
            name,
            f"unsafe source filename: {name!r}",
        )
    return name


def acquire_standard_dges_vintage(
    year: int,
    *,
    raw_root: Path,
    timeout_seconds: float = 60.0,
    overwrite: bool = False,
) -> pd.DataFrame:
    """Discover and download the three standard first-phase DGES source families.

    The function is intended for verified standard vintages. Every source is
    written to an immutable year directory with its adjacent JSON receipt. The
    returned DataFrame is an acquisition log suitable for a release manifest.
    """

    if year < 1997 or year > 2025:
        raise ValueError("standard annual acquisition is registered only for 1997..2025")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    discovered = discover_documents(year, timeout_seconds=timeout_seconds)
    missing = [key for key in STANDARD_REQUIRED_DOCUMENTS if key not in discovered]
    if missing:
        raise MissingDataError(
            "DGES annual documents",
            f"DGES annual index is missing required documents: {missing}",
        )

    year_dir = raw_root / "dges" / str(year)
    rows: list[dict[str, object]] = []
    for document_type in STANDARD_REQUIRED_DOCUMENTS:
        url = discovered[document_type]
        filename = _safe_remote_filename(url, fallback=f"{document_type}.bin")
        receipt = fetch_with_receipt(
            url,
            year_dir / filename,
            timeout_seconds=timeout_seconds,
            overwrite=overwrite,
        )
        row = asdict(receipt)
        row["path"] = str(receipt.path)
        row["year"] = year
        row["document_type"] = document_type
        rows.append(row)

    return pd.DataFrame.from_records(rows).sort_values("document_type").reset_index(drop=True)
