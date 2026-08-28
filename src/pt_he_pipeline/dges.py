"""DGES source discovery and institution-programme index helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from pt_he_pipeline.types import DgesPairReference

_DGES_ANNUAL_TEMPLATE = "https://www.dges.gov.pt/guias/pdfs/statcol/{year}/"
_DGES_PAIR_INDEX_TEMPLATE = (
    "https://www.dges.gov.pt/guias/pdfs/statce/col{yy:02d}f{phase}/index.htm"
)
_PAIR_FILENAME_RE = re.compile(
    r"(?:ec\d{2}(?:f\d)?_)?(?P<institution>[0-9A-Za-z]{4})(?P<course>[0-9A-Za-z]{4})\.pdf$",
    flags=re.IGNORECASE,
)

_DOCUMENT_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "mobility": ("distrito", "1ª opção", "distrito de colocação"),
    "pair_statistics_all": ("estatística por par estabelecimento/curso", "todos os pares"),
    "last_placed_grades": ("classificações dos últimos colocados",),
    "placement_summary": ("resumo da colocação",),
}


def annual_statistics_url(year: int) -> str:
    """Return the canonical annual DGES statistics index URL."""

    if year < 1990 or year > 2100:
        raise ValueError("year is outside a plausible range")
    return _DGES_ANNUAL_TEMPLATE.format(year=year)


def pair_statistics_index_url(year: int, phase: int = 1) -> str:
    """Return the DGES detailed pair-statistics index URL.

    The ``statce`` URL convention has been verified for historical and recent
    first-phase pages. A source manifest records which vintages are actually
    verified before acquisition is attempted.
    """

    if year < 2000 or year > 2099:
        raise ValueError("year must be in the range 2000..2099")
    if phase not in {1, 2, 3}:
        raise ValueError("phase must be 1, 2 or 3")
    return _DGES_PAIR_INDEX_TEMPLATE.format(yy=year % 100, phase=phase)


def discover_documents_from_html(html: str, *, base_url: str) -> dict[str, str]:
    """Discover known DGES document links from an annual index HTML page.

    Matching uses anchor text rather than filenames because historical naming
    conventions may change.
    """

    if not html.strip():
        raise ValueError("html must not be empty")
    if not base_url.startswith(("https://", "http://")):
        raise ValueError("base_url must use http or https")

    soup = BeautifulSoup(html, "html.parser")
    discovered: dict[str, str] = {}

    for anchor in soup.find_all("a", href=True):
        text = " ".join(anchor.get_text(" ", strip=True).casefold().split())
        href = str(anchor["href"])
        for key, tokens in _DOCUMENT_PATTERNS.items():
            if key in discovered:
                continue
            if all(token.casefold() in text for token in tokens):
                discovered[key] = urljoin(base_url, href)

    return discovered


def discover_documents(year: int, *, timeout_seconds: float = 30.0) -> dict[str, str]:
    """Fetch an annual DGES index and discover its known document links."""

    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    url = annual_statistics_url(year)
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    return discover_documents_from_html(response.text, base_url=url)


def _split_course_and_degree(label: str) -> tuple[str, str | None]:
    """Split ``Course [Degree]`` labels used by the DGES index."""

    match = re.fullmatch(r"(?P<course>.*?)\s*\[(?P<degree>[^\]]+)\]\s*", label.strip())
    if match is None:
        return label.strip(), None
    return match.group("course").strip(), match.group("degree").strip()


def _nearest_institution_label(anchor: Tag, institution_id: str) -> str:
    """Find the closest preceding text containing the institution code."""

    candidate: Tag | None = anchor
    pattern = re.compile(rf"\b{re.escape(institution_id)}\b\s+(?P<name>.+)")

    # Historical pages are simple HTML and commonly put the institution as a
    # preceding text/paragraph. Walk a bounded number of previous elements so
    # malformed pages fail explicitly rather than searching the whole DOM.
    for _ in range(30):
        if candidate is None:
            break
        candidate = candidate.find_previous()
        if candidate is None:
            break
        text = " ".join(candidate.get_text(" ", strip=True).split())
        match = pattern.search(text)
        if match is not None:
            name = match.group("name").strip()
            if name:
                return name
    return ""


def discover_pair_references_from_html(
    html: str,
    *,
    year: int,
    phase: int,
    base_url: str,
) -> list[DgesPairReference]:
    """Parse the DGES ``statce`` index into typed pair references."""

    if not html.strip():
        raise ValueError("html must not be empty")
    if not base_url.startswith(("https://", "http://")):
        raise ValueError("base_url must use http or https")
    if phase not in {1, 2, 3}:
        raise ValueError("phase must be 1, 2 or 3")

    soup = BeautifulSoup(html, "html.parser")
    references: list[DgesPairReference] = []
    seen: set[tuple[str, str]] = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        filename = href.rsplit("/", maxsplit=1)[-1]
        match = _PAIR_FILENAME_RE.search(filename)
        if match is None:
            continue

        institution_id = match.group("institution").upper()
        course_id = match.group("course").upper()
        key = (institution_id, course_id)
        if key in seen:
            continue
        seen.add(key)

        course_name, degree = _split_course_and_degree(anchor.get_text(" ", strip=True))
        references.append(
            DgesPairReference(
                year=year,
                phase=phase,
                institution_id=institution_id,
                course_id=course_id,
                institution_name=_nearest_institution_label(anchor, institution_id),
                course_name=course_name,
                degree=degree,
                url=urljoin(base_url, href),
            )
        )

    return references


def normalise_label(value: str) -> str:
    """Normalise a source label for robust concordance keys."""

    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned.casefold()
