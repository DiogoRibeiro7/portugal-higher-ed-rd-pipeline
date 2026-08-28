from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.dges_placements import normalise_placement_table, parse_placement_text


def test_parse_legacy_placement_rows_with_and_without_cutoff() -> None:
    text = """
0110 0347 Universidade dos Açores Engenharia Zootécnica L 10 1 0 9
0110 0625 Universidade dos Açores Educação de Infância L 20 9 0 164.5 11
"""
    frame = parse_placement_text(text, year=2005, phase=1)
    assert len(frame) == 2
    assert frame.loc[0, "vacancies"] == 10
    assert frame.loc[0, "placements"] == 1
    assert pd.isna(frame.loc[0, "last_placed_general_contingent_grade"])
    assert frame.loc[1, "last_placed_general_contingent_grade"] == pytest.approx(164.5)
    assert frame.loc[1, "remaining_vacancies"] == 11


def test_normalise_excel_like_placement_table() -> None:
    raw = pd.DataFrame(
        {
            "Código Instit.": [140],
            "Código Curso": [8086],
            "Nome da Instituição": ["Universidade dos Açores"],
            "Nome do Curso": ["Medicina Veterinária (Preparatórios)"],
            "Grau": ["PM"],
            "Vagas Iniciais": [23],
            "Colocados": [23],
            "Nota do últ. colocado": [166.7],
            "Vagas Sobrantes": [0],
        }
    )
    result = normalise_placement_table(raw, year=2026, phase=1)
    assert result.loc[0, "institution_id"] == "0140"
    assert result.loc[0, "course_id"] == "8086"
    assert result.loc[0, "vacancies"] == 23
    assert result.loc[0, "last_placed_general_contingent_grade"] == pytest.approx(166.7)
