"""Normalise official DGEEC course-classification exports for Study A."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable, Mapping
from pathlib import Path

import pandas as pd

from pt_he_pipeline.io import sha256_file


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
    if not digits:
        return None
    return digits


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
