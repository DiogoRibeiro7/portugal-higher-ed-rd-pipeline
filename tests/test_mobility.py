from __future__ import annotations

from dataexcept import DataTransformationError
import pytest

from pt_he_pipeline.mobility import (
    DESTINATION_DISTRICTS,
    classify_origin_area,
    parse_mobility_page_text,
    parse_mobility_pdf,
    parse_mobility_row,
)


def test_origin_geography_does_not_force_access_area_into_district() -> None:
    assert classify_origin_area("Lisboa") == "district"
    assert classify_origin_area("R. A. Açores") == "autonomous_region"
    assert classify_origin_area("Tâmega") == "access_area"


def test_parse_complete_mobility_row() -> None:
    counts = list(range(1, len(DESTINATION_DISTRICTS) + 1))
    line = "Aveiro " + " ".join(str(value) for value in counts) + f" {sum(counts)}"
    flows = parse_mobility_row(line, year=2025, flow_type="first_choice")
    assert len(flows) == len(DESTINATION_DISTRICTS)
    assert flows[0].origin_area == "Aveiro"
    assert flows[0].count == 1
    assert flows[-1].count == 20


def test_mobility_row_rejects_shifted_cells_as_transformation_error() -> None:
    counts = [1] * (len(DESTINATION_DISTRICTS) - 1)
    line = "Tâmega " + " ".join(str(value) for value in counts) + f" {sum(counts)}"
    with pytest.raises(DataTransformationError, match="expected"):
        parse_mobility_row(line, year=2003, flow_type="first_choice")


def test_mobility_row_keeps_invalid_flow_type_as_value_error() -> None:
    with pytest.raises(ValueError, match="flow_type"):
        parse_mobility_row("Aveiro 1", year=2025, flow_type="unsupported")


def test_preferred_vintage_selects_contemporaneous_matrix() -> None:
    import pandas as pd

    from pt_he_pipeline.mobility import select_preferred_mobility_vintage

    frame = pd.DataFrame(
        {
            "year": [2024, 2024],
            "source_document_year": [2024, 2025],
            "flow_type": ["first_choice", "first_choice"],
            "origin_area": ["Aveiro", "Aveiro"],
            "origin_area_type": ["district", "district"],
            "destination_district": ["Aveiro", "Aveiro"],
            "count": [1284, 1284],
            "source_sha256": ["a" * 64, "b" * 64],
        }
    )
    result = select_preferred_mobility_vintage(frame)
    assert len(result) == 1
    assert result.loc[0, "source_document_year"] == 2024


def test_parse_mobility_page_text_detects_year_and_first_choice() -> None:
    counts = list(range(1, len(DESTINATION_DISTRICTS) + 1))
    row = "Aveiro " + " ".join(str(value) for value in counts) + f" {sum(counts)}"
    text = "\n".join(
        [
            "ACESSO AO ENSINO SUPERIOR 2024-2025 1ª Fase do Concurso Nacional de Acesso de 2025",
            "Madeira 1ª opção Candidatura Total",
            row,
        ]
    )
    frame = parse_mobility_page_text(text, source_document_year=2025)
    assert frame["year"].nunique() == 1
    assert frame.loc[0, "year"] == 2025
    assert frame.loc[0, "source_document_year"] == 2025
    assert frame.loc[0, "flow_type"] == "first_choice"


def test_mobility_page_classifies_malformed_source_as_transformation_error() -> None:
    text = "Concurso Nacional de Acesso de 2025\nMadeira 1ª opção Candidatura Total"
    with pytest.raises(DataTransformationError, match="no mobility rows were parsed"):
        parse_mobility_page_text(text, source_document_year=2025)


def test_mobility_pdf_wraps_unreadable_pdf_as_transformation_error(tmp_path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a PDF")
    with pytest.raises(DataTransformationError, match="PDF read or text extraction failed"):
        parse_mobility_pdf(path, source_document_year=2025)


def test_mobility_pdf_keeps_missing_file_as_file_error(tmp_path) -> None:
    missing = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError):
        parse_mobility_pdf(missing, source_document_year=2025)
