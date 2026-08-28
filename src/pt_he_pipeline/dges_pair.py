"""Parsers for DGES institution-programme detail statistics."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

from pt_he_pipeline.io import sha256_file
from pt_he_pipeline.types import DgesPairStatistics

_ID_RE = re.compile(r"^[0-9A-Za-z]{4}$")
_NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def _fold(value: str) -> str:
    """Return an accent-insensitive, whitespace-normalised lookup string."""

    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.casefold().split())


def _clean_lines(text: str) -> list[str]:
    return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


def _find_line_index(lines: list[str], needle: str, *, start: int = 0) -> int:
    folded_needle = _fold(needle)
    for index in range(start, len(lines)):
        if folded_needle in _fold(lines[index]):
            return index
    raise ValueError(f"section not found: {needle}")


def _extract_code(line: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:\s*([0-9A-Za-z]{{4}})", line, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"could not parse {label!r} code")
    code = match.group(1).upper()
    if _ID_RE.fullmatch(code) is None:
        raise ValueError(f"invalid DGES code: {code}")
    return code


def _numbers(line: str) -> list[float]:
    return [float(token.replace(",", ".")) for token in _NUMBER_RE.findall(line)]


def _optional_float_after_label(lines: Iterable[str], label: str) -> float | None:
    folded_label = _fold(label)
    for line in lines:
        if _fold(line).startswith(folded_label):
            values = _numbers(line)
            return values[-1] if values else None
    return None


def parse_pair_statistics_text(text: str, *, year: int, phase: int) -> DgesPairStatistics:
    """Parse one text-extracted DGES pair-statistics page.

    The parser uses semantic section markers rather than page coordinates. The
    same core structure is observable in DGES pair sheets from at least 2004
    through recent vintages.
    """

    if not text.strip():
        raise ValueError("text must not be empty")
    if phase not in {1, 2, 3}:
        raise ValueError("phase must be 1, 2 or 3")

    lines = _clean_lines(text)
    institution_index = _find_line_index(lines, "Estabelecimento:")
    course_index = _find_line_index(lines, "Curso Superior:")
    institution_id = _extract_code(lines[institution_index], "Estabelecimento")
    course_id = _extract_code(lines[course_index], "Curso Superior")

    # The standard sheet places institution, course and degree immediately
    # after the two code lines. Some extractors append names to the code lines;
    # in that case the fallbacks below remain explicit rather than guessing.
    metadata_start = max(institution_index, course_index) + 1
    if metadata_start + 1 >= len(lines):
        raise ValueError("pair metadata is incomplete")
    institution_name = lines[metadata_start]
    course_name = lines[metadata_start + 1]
    degree = lines[metadata_start + 2] if metadata_start + 2 < len(lines) else None
    if degree is not None and "distribui" in _fold(degree):
        degree = None

    option_start = _find_line_index(lines, "OPÇÃO CANDIDATURA")
    placement_start = _find_line_index(lines, "ETAPA COLOCAÇÃO", start=option_start + 1)

    first_choice_applicants: int | None = None
    applicants: int | None = None
    placements: int | None = None
    for line in lines[option_start + 1 : placement_start]:
        folded = _fold(line)
        if re.match(r"^1[ªa]\b", line, flags=re.IGNORECASE):
            values = _numbers(line)
            # The initial '1' from '1ª' is captured by the number regex.
            if len(values) < 2:
                raise ValueError("first-choice row is malformed")
            first_choice_applicants = int(values[1])
        elif folded.startswith("total"):
            values = _numbers(line)
            if len(values) >= 2:
                applicants = int(values[0])
                placements = int(values[1])

    if first_choice_applicants is None:
        raise ValueError("first-choice applicant count was not found")
    if applicants is None or placements is None:
        raise ValueError("option-section totals were not found")

    last_grade: float | None = None
    placement_end = len(lines)
    for candidate in ("CURSO DO 12", "DISTRITO/", "MÉDIAS DOS COLOCADOS", "SEXO DOS CANDIDATOS"):
        try:
            placement_end = min(
                placement_end,
                _find_line_index(lines, candidate, start=placement_start + 1),
            )
        except ValueError:
            continue
    for line in lines[placement_start + 1 : placement_end]:
        if re.search(r"\bGeral\b", line, flags=re.IGNORECASE):
            values = _numbers(line)
            if len(values) >= 6:
                last_grade = float(values[-1])
            break

    mean_grade: float | None = None
    try:
        means_start = _find_line_index(lines, "MÉDIAS DOS COLOCADOS")
        mean_grade = _optional_float_after_label(lines[means_start + 1 :], "Nota de candidatura")
    except ValueError:
        # Some historical or phase-specific sheets may omit the means block.
        mean_grade = None

    return DgesPairStatistics(
        year=year,
        phase=phase,
        institution_id=institution_id,
        course_id=course_id,
        institution_name=institution_name,
        course_name=course_name,
        degree=degree,
        applicants=applicants,
        first_choice_applicants=first_choice_applicants,
        placements=placements,
        mean_application_grade_placed=mean_grade,
        last_placed_general_contingent_grade=last_grade,
    )


def extract_pdf_pages(path: Path) -> list[str]:
    """Extract PDF pages with layout-aware text when supported by ``pypdf``."""

    if not path.is_file():
        raise FileNotFoundError(path)
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text(extraction_mode="layout")
        except TypeError:  # pragma: no cover - compatibility with older pypdf.
            text = page.extract_text()
        pages.append(text or "")
    return pages


def parse_pair_statistics_pdf(path: Path, *, year: int, phase: int) -> pd.DataFrame:
    """Parse all pair-statistics pages in a DGES PDF to a DataFrame.

    Unparseable non-data pages are skipped, while a page containing a pair
    code but failing semantic parsing is treated as an error. This prevents a
    cover page from failing the run without silently losing real observations.
    """

    digest = sha256_file(path)
    records: list[dict[str, object]] = []
    for page_number, text in enumerate(extract_pdf_pages(path), start=1):
        if "Estabelecimento:" not in text or "Curso Superior:" not in text:
            continue
        try:
            parsed = parse_pair_statistics_text(text, year=year, phase=phase)
        except ValueError as exc:
            raise ValueError(f"failed to parse pair-statistics page {page_number}: {exc}") from exc
        row = {
            field: getattr(parsed, field)
            for field in parsed.__dataclass_fields__
        }
        row["pair_statistics_source_sha256"] = digest
        row["pair_statistics_source_page"] = page_number
        records.append(row)

    if not records:
        raise ValueError("no DGES pair-statistics pages were parsed")
    return pd.DataFrame.from_records(records)
