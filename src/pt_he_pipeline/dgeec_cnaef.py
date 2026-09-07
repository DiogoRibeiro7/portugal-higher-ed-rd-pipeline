"""Normalise and source-lock official DGEEC course classifications for Study A."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from pt_he_pipeline.io import fetch_with_receipt, sha256_file

_FICHA_BASE_URL = "https://cnaef.dgeec.medu.pt/"
_CLASSIFICATION_PREFIX = {2013: "13", 1997: "97"}


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.casefold().split())


def _normalise_header(value: object) -> str:
    folded = _fold(str(value)).replace("º", "")
    return " ".join(re.sub(r"[^0-9a-z]+", " ", folded).split())


_HEADER_ALIASES: Mapping[str, tuple[str, ...]] = {
    "institution_id": (
        "codigo instituicao",
        "codigo estabelecimento",
        "cod instituicao",
        "cod estabelecimento",
    ),
    "course_id": ("codigo curso", "cod curso"),
    "course_name": ("nome curso", "designacao curso", "curso"),
    "degree": ("grau", "tipo curso"),
    "citef_2013_code": (
        "cite f 2013 codigo",
        "cite f 2013",
        "citef 2013 codigo",
        "citef 2013",
    ),
    "cite_1997_code": (
        "cite 1997 codigo",
        "cite 1997",
        "cnaef codigo",
        "cnaef",
    ),
}


def _match_column(columns: Iterable[object], aliases: tuple[str, ...]) -> object | None:
    normalised = {column: _normalise_header(column) for column in columns}
    for alias in aliases:
        target = _normalise_header(alias)
        for column, label in normalised.items():
            if target == label or target in label:
                return column
    return None


def _normalise_code(value: object) -> str | None:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _normalise_field_code(value: object) -> str | None:
    text = _normalise_code(value)
    if text is None:
        return None
    digits = re.sub(r"\D", "", text)
    return digits or None


def _course_id(value: object) -> str:
    code = _normalise_code(value)
    if code is None or len(code) != 4 or not code.isalnum():
        raise ValueError(f"invalid DGEEC course code: {value!r}")
    return code


def _ficha_lines(html: str) -> list[str]:
    if not html.strip():
        raise ValueError("DGEEC ficha HTML must not be empty")
    soup = BeautifulSoup(html, "html.parser")
    return [" ".join(value.split()) for value in soup.stripped_strings if value.strip()]


def _value_after_label(lines: list[str], label: str) -> str:
    target = _fold(label)
    for index, line in enumerate(lines[:-1]):
        if _fold(line) == target:
            return lines[index + 1]
    raise ValueError(f"missing DGEEC ficha field: {label}")


def _split_code_label(value: str, *, field: str) -> tuple[str, str]:
    match = re.match(r"^([0-9A-Za-z]+)\s*-\s*(.+)$", value)
    if match is None:
        raise ValueError(f"invalid DGEEC ficha {field}: {value!r}")
    return match.group(1).upper(), match.group(2).strip()


def _classification_block(
    lines: list[str], *, classification_version: int
) -> tuple[str, tuple[str, ...]]:
    """Return the provider's principal and secondary field codes for one ficha."""

    area_label = f"Área CNAEF {classification_version}"
    target = _fold(area_label)
    start: int | None = None
    for index, line in enumerate(lines):
        if _fold(line) == target:
            start = index + 1
            break
    if start is None:
        raise ValueError(f"missing DGEEC ficha field: {area_label}")

    principal: str | None = None
    secondary: list[str] = []
    index = start
    while index < len(lines):
        label = _fold(lines[index])
        if label in {"url direto", "mostrar estabelecimentos", "estabelecimentos"}:
            break
        if label in {"principal", "secundaria"}:
            if index + 1 >= len(lines):
                raise ValueError(f"missing DGEEC ficha value after {lines[index]}")
            code, _ = _split_code_label(lines[index + 1], field=lines[index])
            normalised = _normalise_field_code(code)
            if normalised is None:
                raise ValueError("DGEEC ficha classification code is missing")
            if label == "principal":
                if principal is not None:
                    raise ValueError("multiple principal DGEEC classifications")
                principal = normalised
            else:
                secondary.append(normalised)
            index += 2
            continue
        index += 1

    if principal is None:
        raise ValueError("DGEEC ficha principal classification is missing")
    return principal, tuple(secondary)


def course_ficha_url(course_id: object, *, classification_version: int = 2013) -> str:
    """Return the stable DGEEC ficha URL for one course and classification version."""

    try:
        prefix = _CLASSIFICATION_PREFIX[classification_version]
    except KeyError as exc:
        raise ValueError("classification_version must be 2013 or 1997") from exc
    code = _course_id(course_id)
    return f"{_FICHA_BASE_URL}?accao=Ficha&cod={prefix}{code}"


def parse_course_ficha_html(
    html: str,
    *,
    classification_version: int = 2013,
    expected_course_id: str | None = None,
    source_url: str | None = None,
) -> dict[str, object]:
    """Parse one official DGEEC per-course classification ficha."""

    if classification_version not in _CLASSIFICATION_PREFIX:
        raise ValueError("classification_version must be 2013 or 1997")
    lines = _ficha_lines(html)

    course_code, course_name = _split_code_label(
        _value_after_label(lines, "Curso"), field="course"
    )
    course_code = _course_id(course_code)
    if expected_course_id is not None and course_code != _course_id(expected_course_id):
        raise ValueError(
            f"DGEEC ficha course mismatch: expected {expected_course_id}, got {course_code}"
        )

    _, degree = _split_code_label(_value_after_label(lines, "Diploma"), field="diploma")
    principal_code, secondary_codes = _classification_block(
        lines, classification_version=classification_version
    )

    citef_2013_code = principal_code if classification_version == 2013 else pd.NA
    cite_1997_code = principal_code if classification_version == 1997 else pd.NA
    return {
        "course_id": course_code,
        "course_name": course_name,
        "degree": degree,
        "citef_2013_code": citef_2013_code,
        "cite_1997_code": cite_1997_code,
        "secondary_classification_codes": "|".join(secondary_codes),
        "isced_f_2013_2digit": (
            principal_code[:2] if classification_version == 2013 else pd.NA
        ),
        "classification_source_url": source_url,
    }


def parse_course_ficha_file(
    path: Path,
    *,
    classification_version: int = 2013,
    expected_course_id: str | None = None,
    source_url: str | None = None,
) -> dict[str, object]:
    """Parse a source-locked DGEEC ficha and attach its SHA-256 digest."""

    if not path.is_file():
        raise FileNotFoundError(path)
    record = parse_course_ficha_html(
        path.read_text(encoding="utf-8", errors="replace"),
        classification_version=classification_version,
        expected_course_id=expected_course_id,
        source_url=source_url,
    )
    record["classification_source_sha256"] = sha256_file(path)
    return record


def fetch_course_ficha(
    course_id: object,
    output: Path,
    *,
    classification_version: int = 2013,
    overwrite: bool = False,
) -> dict[str, object]:
    """Source-lock one DGEEC ficha with a receipt and return its parsed classification."""

    code = _course_id(course_id)
    url = course_ficha_url(code, classification_version=classification_version)
    fetch_with_receipt(url, output, overwrite=overwrite)
    return parse_course_ficha_file(
        output,
        classification_version=classification_version,
        expected_course_id=code,
        source_url=url,
    )


def normalise_course_classification_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalise one official DGEEC classification table by header semantics."""

    if frame.empty:
        raise ValueError("classification table must not be empty")

    mapping: dict[str, object] = {}
    for target, aliases in _HEADER_ALIASES.items():
        source = _match_column(frame.columns, aliases)
        if source is not None:
            mapping[target] = source

    required = {"course_id", "course_name", "citef_2013_code"}
    missing = sorted(required.difference(mapping))
    if missing:
        observed = [str(column) for column in frame.columns]
        raise ValueError(f"required DGEEC columns not found: {missing}; observed={observed}")

    result = pd.DataFrame(index=frame.index)
    for target in _HEADER_ALIASES:
        source = mapping.get(target)
        result[target] = frame[source] if source is not None else pd.NA

    result["institution_id"] = result["institution_id"].map(_normalise_code).astype("string")
    result["course_id"] = result["course_id"].map(_normalise_code).astype("string")
    result["course_name"] = result["course_name"].astype("string").str.strip()
    result["degree"] = result["degree"].astype("string").str.strip()
    result["citef_2013_code"] = (
        result["citef_2013_code"].map(_normalise_field_code).astype("string")
    )
    result["cite_1997_code"] = (
        result["cite_1997_code"].map(_normalise_field_code).astype("string")
    )
    result["isced_f_2013_2digit"] = result["citef_2013_code"].str[:2]

    result = result.dropna(subset=["course_id", "course_name", "citef_2013_code"])
    result = result.loc[result["course_name"].str.len() > 0].reset_index(drop=True)
    if result.empty:
        raise ValueError("no usable DGEEC classification rows remain after normalisation")
    return result


def parse_course_classification_excel(path: Path) -> pd.DataFrame:
    """Read an official DGEEC XLSX export and attach source provenance."""

    if not path.is_file():
        raise FileNotFoundError(path)
    frame = pd.read_excel(path)
    result = normalise_course_classification_table(frame)
    result["classification_source_sha256"] = sha256_file(path)
    return result
