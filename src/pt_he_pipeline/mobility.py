"""DGES first-choice and placement mobility parsing helpers."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd
from dataexcept import DataTransformationError

from pt_he_pipeline.dges_pair import extract_pdf_pages
from pt_he_pipeline.io import sha256_file
from pt_he_pipeline.types import MobilityFlow

DESTINATION_DISTRICTS: tuple[str, ...] = (
    "Aveiro",
    "Beja",
    "Braga",
    "Bragança",
    "Castelo Branco",
    "Coimbra",
    "Évora",
    "Faro",
    "Guarda",
    "Leiria",
    "Lisboa",
    "Portalegre",
    "Porto",
    "Santarém",
    "Setúbal",
    "Viana do Castelo",
    "Vila Real",
    "Viseu",
    "R. A. Açores",
    "R. A. Madeira",
)
_DISTRICT_KEYS = {" ".join(name.casefold().split()) for name in DESTINATION_DISTRICTS}
_INTEGER_RE = re.compile(r"\b\d+\b")
_YEAR_RE = re.compile(r"Concurso\s+Nacional\s+de\s+Acesso\s+de\s+(20\d{2}|19\d{2})", re.I)


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char)).casefold().split()
    )


def classify_origin_area(label: str) -> str:
    """Classify a DGES origin label without forcing legacy CAE/GAES areas into districts."""

    key = " ".join(label.casefold().split())
    if key in _DISTRICT_KEYS:
        if key.startswith("r. a."):
            return "autonomous_region"
        return "district"
    return "access_area"


def _parse_mobility_row(
    line: str,
    *,
    year: int,
    flow_type: str,
    source_document_year: int | None,
    destinations: Sequence[str],
) -> list[MobilityFlow]:
    matches = list(_INTEGER_RE.finditer(line))
    required_numbers = len(destinations) + 1
    if len(matches) != required_numbers:
        raise ValueError(
            f"expected {required_numbers} integer cells including total, found {len(matches)}"
        )

    origin = line[: matches[0].start()].strip()
    if not origin:
        raise ValueError("origin area is missing")
    if _fold(origin) == "total":
        raise ValueError("aggregate total row is not an origin flow")

    values = [int(match.group()) for match in matches]
    cells, reported_total = values[:-1], values[-1]
    if sum(cells) != reported_total:
        raise ValueError(
            "mobility row total mismatch for "
            f"{origin!r}: cells={sum(cells)}, reported={reported_total}"
        )

    area_type = classify_origin_area(origin)
    document_year = year if source_document_year is None else source_document_year
    return [
        MobilityFlow(
            year=year,
            source_document_year=document_year,
            flow_type=flow_type,
            origin_area=origin,
            origin_area_type=area_type,
            destination_district=destination,
            count=count,
        )
        for destination, count in zip(destinations, cells, strict=True)
    ]


def parse_mobility_row(
    line: str,
    *,
    year: int,
    flow_type: str,
    source_document_year: int | None = None,
    destinations: Sequence[str] = DESTINATION_DISTRICTS,
) -> list[MobilityFlow]:
    """Parse one flattened mobility row with complete destination cells."""

    if flow_type not in {"first_choice", "placement"}:
        raise ValueError("flow_type must be 'first_choice' or 'placement'")
    if not line.strip():
        raise DataTransformationError("parse_mobility_row", "line must not be empty")

    try:
        return _parse_mobility_row(
            line,
            year=year,
            flow_type=flow_type,
            source_document_year=source_document_year,
            destinations=destinations,
        )
    except ValueError as exc:
        raise DataTransformationError("parse_mobility_row", str(exc)) from exc


def parse_mobility_rows(
    lines: Iterable[str],
    *,
    year: int,
    flow_type: str,
    source_document_year: int | None = None,
    destinations: Sequence[str] = DESTINATION_DISTRICTS,
) -> pd.DataFrame:
    """Parse all complete mobility rows from an extracted matrix section."""

    if flow_type not in {"first_choice", "placement"}:
        raise ValueError("flow_type must be 'first_choice' or 'placement'")

    records: list[dict[str, object]] = []
    failures: list[str] = []
    for line in lines:
        if _fold(line).startswith("total "):
            continue
        if len(_INTEGER_RE.findall(line)) < len(destinations):
            continue
        try:
            flows = parse_mobility_row(
                line,
                year=year,
                flow_type=flow_type,
                source_document_year=source_document_year,
                destinations=destinations,
            )
        except DataTransformationError as exc:
            failures.append(str(exc))
            continue
        records.extend(
            {field: getattr(flow, field) for field in flow.__dataclass_fields__}
            for flow in flows
        )

    if failures:
        examples = "; ".join(failures[:3])
        raise DataTransformationError(
            "parse_mobility_rows",
            f"one or more candidate mobility rows were malformed: {examples}",
        )
    if not records:
        raise DataTransformationError(
            "parse_mobility_rows",
            "no mobility rows were parsed",
        )
    return pd.DataFrame.from_records(records)


def _page_flow_type(text: str) -> str:
    folded = _fold(text)
    if "1a opcao candidatura total" in folded or "1a opcao" in folded:
        return "first_choice"
    if "colocacao candidatura total" in folded:
        return "placement"
    raise ValueError("could not identify mobility flow type from page")


def _page_data_year(text: str) -> int:
    match = _YEAR_RE.search(text)
    if match is None:
        raise ValueError("could not identify mobility data year from page")
    return int(match.group(1))


def parse_mobility_page_text(
    text: str,
    *,
    source_document_year: int,
) -> pd.DataFrame:
    """Parse one DGES mobility-matrix page from extracted text."""

    if not text.strip():
        raise DataTransformationError(
            "parse_mobility_page_text",
            "text must not be empty",
        )
    try:
        year = _page_data_year(text)
        flow_type = _page_flow_type(text)
        return parse_mobility_rows(
            text.splitlines(),
            year=year,
            flow_type=flow_type,
            source_document_year=source_document_year,
        )
    except ValueError as exc:
        raise DataTransformationError("parse_mobility_page_text", str(exc)) from exc


def parse_mobility_pdf(path: Path, *, source_document_year: int) -> pd.DataFrame:
    """Parse all matrices in a DGES comparative mobility PDF."""

    digest = sha256_file(path)
    try:
        pages = extract_pdf_pages(path)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise DataTransformationError(
            "parse_mobility_pdf",
            f"PDF read or text extraction failed: {exc}",
        ) from exc

    chunks: list[pd.DataFrame] = []
    for page_number, text in enumerate(pages, start=1):
        try:
            frame = parse_mobility_page_text(
                text,
                source_document_year=source_document_year,
            )
        except DataTransformationError as exc:
            folded = _fold(text)
            looks_like_data = bool(_YEAR_RE.search(text)) or "candidatura total" in folded
            if looks_like_data:
                raise DataTransformationError(
                    "parse_mobility_pdf",
                    f"page {page_number}: {exc}",
                ) from exc
            continue
        frame["source_sha256"] = digest
        frame["source_page"] = page_number
        chunks.append(frame)

    if not chunks:
        raise DataTransformationError(
            "parse_mobility_pdf",
            "no mobility matrices were parsed from PDF",
        )
    return pd.concat(chunks, ignore_index=True)


def select_preferred_mobility_vintage(frame: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate comparative mobility matrices across annual source files."""

    required = {
        "year",
        "source_document_year",
        "flow_type",
        "origin_area",
        "destination_district",
        "count",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing mobility vintage columns: {missing}")
    if frame.empty:
        raise ValueError("frame must not be empty")

    keys = ["year", "flow_type", "origin_area", "destination_district"]
    working = frame.copy()
    working["_distance"] = (
        pd.to_numeric(working["source_document_year"], errors="raise")
        - pd.to_numeric(working["year"], errors="raise")
    ).abs()
    working = working.sort_values([*keys, "_distance", "source_document_year"])

    selected: list[pd.Series] = []
    for _, group in working.groupby(keys, sort=False, dropna=False):
        best_distance = group["_distance"].min()
        candidates = group.loc[group["_distance"] == best_distance]
        if len(candidates) > 1 and candidates["count"].nunique(dropna=False) > 1:
            raise ValueError("conflicting mobility cells at the same preferred vintage distance")
        selected.append(candidates.sort_values("source_document_year").iloc[0])

    return pd.DataFrame(selected).drop(columns="_distance").reset_index(drop=True)


def comparable_same_district_flows(frame: pd.DataFrame) -> pd.DataFrame:
    """Return district/autonomous-region origins suitable for diagonal metrics."""

    required = {"origin_area", "origin_area_type", "destination_district", "count"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"missing mobility columns: {missing}")
    return frame.loc[
        frame["origin_area_type"].isin(["district", "autonomous_region"])
    ].copy()
