from __future__ import annotations

import pytest
from dataexcept import DataTransformationError

from pt_he_pipeline.dges_pair import (
    parse_pair_statistics_pdf,
    parse_pair_statistics_text,
)


TEXT_2024 = """
ACESSO AO ENSINO SUPERIOR 2024 1ª Fase do Concurso Nacional de Acesso
Estabelecimento: 0160
Curso Superior: 8083
Universidade dos Açores - Faculdade de Ciências e Tecnologia
Ciclo Básico de Medicina
Prep. Mestrado Integrado
DISTRIBUIÇÕES DE NOTAS DE CANDIDATURA
OPÇÃO CANDIDATURA
Opção Cands. % Cols. %
1ª 33 22 8 44
2ª 34 8 8 16
Total 401 50
ETAPA COLOCAÇÃO (contingente)
Etapa Colocação Cands. % Cols. % Nota
2 Açores Pr.Reg. 1 22 22 5 44 159.3
17 Geral 401 27 100 54 176.5
Total 458 50
CURSO DO 12º ANO
DISTRITO/CAE DE CANDIDATURA
Total 401 50
MÉDIAS DOS COLOCADOS
Nota de candidatura 176.2
Prova de ingresso 168.3
SEXO DOS CANDIDATOS
"""

TEXT_2004 = """
ACESSO AO ENSINO SUPERIOR 2004 1ª Fase do Concurso Nacional de Acesso
Estabelecimento: 0110
Curso Superior: 0213
Universidade dos Açores - Angra do Heroísmo
Engenharia do Ambiente
Licenciatura
DISTRIBUIÇÕES DE NOTAS DE CANDIDATURA
OPÇÃO CANDIDATURA
Opção Cands. % Cols. %
1ª 1 1 7 100
2ª 2 0 13 0
Total 15 1
ETAPA COLOCAÇÃO (contingente)
Etapa Colocação Cands. % Cols. % Nota
2 Açores Pr.Reg. 1 8 1 53 100 136.0
17 Geral 15 0 100 0
Total 43 1
CURSO DO 12º ANO
DISTRITO/CAE DE CANDIDATURA
Total 15 1
MÉDIAS DOS COLOCADOS
Nota de candidatura 136,0
Prova de ingresso 115,4
SEXO DOS CANDIDATOS
"""


def test_parse_recent_pair_statistics() -> None:
    parsed = parse_pair_statistics_text(TEXT_2024, year=2024, phase=1)
    assert parsed.institution_id == "0160"
    assert parsed.course_id == "8083"
    assert parsed.applicants == 401
    assert parsed.first_choice_applicants == 33
    assert parsed.placements == 50
    assert parsed.mean_application_grade_placed == pytest.approx(176.2)
    assert parsed.last_placed_general_contingent_grade == pytest.approx(176.5)


def test_parse_legacy_pair_statistics_without_general_cutoff() -> None:
    parsed = parse_pair_statistics_text(TEXT_2004, year=2004, phase=1)
    assert parsed.applicants == 15
    assert parsed.first_choice_applicants == 1
    assert parsed.placements == 1
    assert parsed.mean_application_grade_placed == pytest.approx(136.0)
    assert parsed.last_placed_general_contingent_grade is None


def test_pair_parser_classifies_malformed_source_as_transformation_error() -> None:
    malformed = "Estabelecimento: 0160\nCurso Superior: 8083\n"
    with pytest.raises(DataTransformationError, match="pair metadata is incomplete"):
        parse_pair_statistics_text(malformed, year=2024, phase=1)


def test_pair_parser_keeps_invalid_phase_as_value_error() -> None:
    with pytest.raises(ValueError, match="phase must be"):
        parse_pair_statistics_text(TEXT_2024, year=2024, phase=4)


def test_pair_pdf_wraps_unreadable_pdf_as_transformation_error(tmp_path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not a PDF")
    with pytest.raises(DataTransformationError, match="PDF read or text extraction failed"):
        parse_pair_statistics_pdf(path, year=2024, phase=1)


def test_pair_pdf_validates_phase_before_file_access(tmp_path) -> None:
    missing = tmp_path / "missing.pdf"
    with pytest.raises(ValueError, match="phase must be"):
        parse_pair_statistics_pdf(missing, year=2024, phase=4)


def test_pair_pdf_keeps_missing_file_as_file_error(tmp_path) -> None:
    missing = tmp_path / "missing.pdf"
    with pytest.raises(FileNotFoundError):
        parse_pair_statistics_pdf(missing, year=2024, phase=1)
