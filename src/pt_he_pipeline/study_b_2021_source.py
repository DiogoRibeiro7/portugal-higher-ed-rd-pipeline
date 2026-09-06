"""Parse the registered Study B 2020-2021 DGES comparative source blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

MEASURES = (
    "vacancies",
    "applicants",
    "first_choice_applicants",
    "placements",
    "first_choice_placements",
    "last_placed_general_contingent_grade",
    "mean_application_grade_placed",
    "mean_entrance_exam_grade_placed",
    "mean_secondary_grade_placed",
)

_HEADING_RE = re.compile(r"^\s*(?:[A-Z]\d{3}|\d{4})\s+.+?\s+\[Licenciatura\]\s*$", re.MULTILINE)
_INSTITUTION_RE = re.compile(r"^\s*(\d{4})\s+(.+)$")
_CODE_NOTE_RE = re.compile(
    r"C[oó]digo em 2020:\s*(?:\d{4}/)?([A-Z]?\d{3,4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ComparativeRow:
    programme_code: str
    institution_code: str
    year: int
    values: tuple[Decimal, ...]
    prior_programme_code: str | None = None

    def as_measure_dict(self) -> dict[str, Decimal]:
        """Return the nine registered measures keyed by canonical names."""

        return dict(zip(MEASURES, self.values, strict=True))


def programme_section(text: str, *, code: str, name: str) -> str:
    """Return exactly one registered programme section from ``pdftotext -layout`` output."""

    marker = re.compile(
        rf"^\s*{re.escape(code)}\s+{re.escape(name)}\s+\[Licenciatura\]\s*$",
        re.MULTILINE,
    )
    match = marker.search(text)
    if match is None:
        raise ValueError(f"missing registered programme heading: {code} {name}")
    next_match = _HEADING_RE.search(text, match.end())
    end = next_match.start() if next_match else len(text)
    return text[match.end() : end]


def _decimal_tokens(line: str) -> tuple[Decimal, ...]:
    values: list[Decimal] = []
    for token in line.split():
        try:
            values.append(Decimal(token))
        except InvalidOperation:
            continue
    return tuple(values)


def parse_comparative_section(
    section: str,
    *,
    programme_code: str,
) -> tuple[ComparativeRow, ...]:
    """Parse institution-level 2020/2021 rows from one programme section.

    The DGES layout prints the two vacancy values separately, followed by the
    eight remaining measures for 2020 and 2021. A repeated trailing grade is
    present later in each block and is intentionally ignored.
    """

    lines = section.splitlines()
    rows: list[ComparativeRow] = []
    index = 0
    while index < len(lines):
        match = _INSTITUTION_RE.match(lines[index])
        if match is None:
            index += 1
            continue

        institution_code = match.group(1)
        block_end = index + 1
        while block_end < len(lines):
            if _INSTITUTION_RE.match(lines[block_end]) or _HEADING_RE.match(lines[block_end]):
                break
            block_end += 1
        block = lines[index:block_end]
        joined = " ".join(block)
        prior_match = _CODE_NOTE_RE.search(joined)
        prior_code = prior_match.group(1) if prior_match else None

        try:
            marker = next(i for i, line in enumerate(block) if "%var." in line)
        except StopIteration:
            index = block_end
            continue

        numeric_lines = [_decimal_tokens(line) for line in block[marker + 1 :]]
        numeric_lines = [values for values in numeric_lines if values]
        if len(numeric_lines) < 4:
            raise ValueError(
                f"{programme_code}/{institution_code}: incomplete comparative block"
            )

        vacancies_2020 = numeric_lines[0]
        vacancies_2021 = numeric_lines[1]
        measures_2020 = numeric_lines[2]
        measures_2021 = numeric_lines[3]
        if len(vacancies_2020) != 1 or len(vacancies_2021) != 1:
            raise ValueError(
                f"{programme_code}/{institution_code}: ambiguous vacancy rows"
            )
        if len(measures_2020) < 8 or len(measures_2021) < 8:
            raise ValueError(
                f"{programme_code}/{institution_code}: expected eight non-vacancy measures"
            )

        rows.extend(
            (
                ComparativeRow(
                    programme_code=programme_code,
                    institution_code=institution_code,
                    year=2020,
                    values=(vacancies_2020[0], *measures_2020[:8]),
                    prior_programme_code=prior_code,
                ),
                ComparativeRow(
                    programme_code=programme_code,
                    institution_code=institution_code,
                    year=2021,
                    values=(vacancies_2021[0], *measures_2021[:8]),
                    prior_programme_code=prior_code,
                ),
            )
        )
        index = block_end

    if not rows:
        raise ValueError(f"no comparative rows parsed for programme {programme_code}")
    return tuple(rows)
