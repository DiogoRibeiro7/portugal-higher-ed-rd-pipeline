"""Parsers for DGES vacancy, placement and cut-off tables."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

from pt_he_pipeline.dges_pair import extract_pdf_pages
from pt_he_pipeline.io import sha256_file
from pt_he_pipeline.types import DgesPlacementRecord

_NUMBER_TOKEN_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
_CODE_RE = re.compile(r"^[0-9A-Za-z]{4}$")


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.casefold().split())


def _to_number(token: str) -> float:
    return float(token.replace(",", "."))


def _parse_row_tokens(tokens: list[str], *, year: int, phase: int) -> DgesPlacementRecord | None:
    """Parse one whitespace-tokenised placement row.

    The PDF column count changed over time. The stable anchors are the two
    four-character codes, the degree token and the numeric tail. The first
    numeric value after degree is the initial vacancy count, the next is the
    placed count, and the final value is remaining capacity. The penultimate
    decimal-like value is the general-contingent cut-off when present.
    """

    if (
        len(tokens) < 8
        or _CODE_RE.fullmatch(tokens[0]) is None
        or _CODE_RE.fullmatch(tokens[1]) is None
    ):
        return None

    tail_start: int | None = None
    for index in range(3, len(tokens)):
        tail = tokens[index:]
        if len(tail) >= 3 and all(_NUMBER_TOKEN_RE.fullmatch(token) for token in tail):
            tail_start = index
            break
    if tail_start is None or tail_start < 3:
        return None

    degree_index = tail_start - 1
    numeric_tail = tokens[tail_start:]

    vacancies = int(_to_number(numeric_tail[0]))
    placements = int(_to_number(numeric_tail[1]))
    remaining = int(_to_number(numeric_tail[-1]))

    # The cut-off is normally the penultimate numeric column. A blank cut-off
    # makes the remaining-vacancy value the final token with only integer
    # control columns before it; treating a positive integer control field as
    # a grade would be unsafe, so only plausible 0--200 grade values are kept.
    last_grade: float | None = None
    if len(numeric_tail) >= 4:
        grade_token = numeric_tail[-2]
        candidate = _to_number(grade_token)
        # DGES cut-offs are printed with one decimal place in the verified PDF
        # vintages. Requiring an explicit decimal mark avoids mistaking a
        # control-count column for a grade when the cut-off cell is blank.
        if ("." in grade_token or "," in grade_token) and 0.0 < candidate <= 200.0:
            last_grade = candidate

    institution_name = " ".join(tokens[2:degree_index]).strip()
    course_name = ""
    # The flattened text does not provide an unambiguous institution/course
    # boundary. These labels are later filled from the pair-statistics table;
    # raw row parsing therefore avoids inventing that boundary.
    return DgesPlacementRecord(
        year=year,
        phase=phase,
        institution_id=tokens[0].upper(),
        course_id=tokens[1].upper(),
        institution_name=institution_name,
        course_name=course_name,
        degree=tokens[degree_index],
        vacancies=vacancies,
        placements=placements,
        last_placed_general_contingent_grade=last_grade,
        remaining_vacancies=remaining,
    )


def parse_placement_text(text: str, *, year: int, phase: int) -> pd.DataFrame:
    """Parse layout-preserved placement-table text into canonical fields.

    This parser is intentionally conservative. It captures rows for which the
    stable structural anchors can be identified and leaves labels to the pair
    statistics join. Coverage reporting makes any lost rows visible.
    """

    if not text.strip():
        raise ValueError("text must not be empty")
    rows: list[dict[str, object]] = []
    for line in text.splitlines():
        tokens = line.split()
        parsed = _parse_row_tokens(tokens, year=year, phase=phase)
        if parsed is None:
            continue
        rows.append({field: getattr(parsed, field) for field in parsed.__dataclass_fields__})
    if not rows:
        raise ValueError("no placement rows were parsed")
    return pd.DataFrame.from_records(rows)


def parse_placement_pdf(path: Path, *, year: int, phase: int) -> pd.DataFrame:
    """Parse a DGES placement/cut-off PDF and attach raw-source provenance."""

    digest = sha256_file(path)
    chunks: list[pd.DataFrame] = []
    for page_number, text in enumerate(extract_pdf_pages(path), start=1):
        try:
            frame = parse_placement_text(text, year=year, phase=phase)
        except ValueError:
            continue
        frame["placement_source_page"] = page_number
        chunks.append(frame)
    if not chunks:
        raise ValueError("no placement rows were parsed from PDF")
    result = pd.concat(chunks, ignore_index=True)
    result["placement_source_sha256"] = digest
    return result


def _normalise_header(value: object) -> str:
    """Normalise a tabular header while ignoring punctuation variants."""

    folded = _fold(str(value)).replace("º", "")
    return " ".join(re.sub(r"[^0-9a-z]+", " ", folded).split())


_HEADER_ALIASES: Mapping[str, tuple[str, ...]] = {
    "institution_id": ("codigo instit", "codigo estab", "cod instit", "cod estab"),
    "course_id": ("codigo curso", "cod curso"),
    "institution_name": ("nome da instituicao", "nome do estabelecimento"),
    "course_name": ("nome do curso",),
    "degree": ("grau",),
    "vacancies": ("vagas iniciais", "vagas colocadas a concurso", "vagas"),
    "placements": ("colocados",),
    "last_placed_general_contingent_grade": (
        "nota do ult colocado",
        "nota do ultimo colocado",
        "nota do ult colocado cont geral",
    ),
    "remaining_vacancies": ("vagas sobrantes", "sobras para 2 fase"),
}


def _match_column(columns: Iterable[object], aliases: tuple[str, ...]) -> object | None:
    normalised = {column: _normalise_header(column) for column in columns}
    for alias in aliases:
        folded_alias = _normalise_header(alias)
        for column, label in normalised.items():
            if folded_alias in label:
                return column
    return None


def _normalise_code(value: object) -> str | None:
    """Normalise a DGES four-character code, preserving alphanumeric IDs."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    if text.isdigit():
        return text.zfill(4)
    return text if len(text) == 4 else None


def normalise_placement_table(frame: pd.DataFrame, *, year: int, phase: int) -> pd.DataFrame:
    """Normalise an official DGES Excel/HTML placement table by header semantics."""

    if frame.empty:
        raise ValueError("placement table must not be empty")
    mapping: dict[str, object] = {}
    for target, aliases in _HEADER_ALIASES.items():
        source = _match_column(frame.columns, aliases)
        if source is not None:
            mapping[target] = source

    required = {"institution_id", "course_id", "vacancies", "placements"}
    missing = sorted(required.difference(mapping))
    if missing:
        observed = [str(column) for column in frame.columns]
        raise ValueError(f"required DGES columns not found: {missing}; observed={observed}")

    result = pd.DataFrame(index=frame.index)
    result["year"] = int(year)
    result["phase"] = int(phase)
    for target in _HEADER_ALIASES:
        source = mapping.get(target)
        result[target] = frame[source] if source is not None else pd.NA

    for code in ("institution_id", "course_id"):
        result[code] = result[code].map(_normalise_code).astype("string")
    for column in ("vacancies", "placements", "remaining_vacancies"):
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Int64")
    result["last_placed_general_contingent_grade"] = pd.to_numeric(
        result["last_placed_general_contingent_grade"], errors="coerce"
    )
    return result.dropna(
        subset=["institution_id", "course_id", "vacancies", "placements"]
    ).reset_index(drop=True)


def parse_placement_excel(path: Path, *, year: int, phase: int) -> pd.DataFrame:
    """Read and normalise a DGES Excel result file.

    Legacy ``.xls`` files require the optional ``xlrd`` dependency declared by
    the project. Modern ``.xlsx`` files use ``openpyxl`` through pandas.
    """

    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_excel(path)
    result = normalise_placement_table(frame, year=year, phase=phase)
    result["placement_source_sha256"] = sha256_file(path)
    return result
