from __future__ import annotations

import pandas as pd
import pytest
from dataexcept import MissingColumnError

from pt_he_pipeline.concordance import build_concordance_candidates, concordance_key


def test_concordance_key_is_accent_insensitive() -> None:
    assert concordance_key("Ciências e Tecnologia") == "ciencias e tecnologia"


def test_concordance_candidates_preserve_raw_ids() -> None:
    frame = pd.DataFrame(
        {
            "year": [2024, 2025],
            "institution_id": ["0160", "0160"],
            "course_id": ["8083", "8083"],
            "institution_name": ["Universidade dos Açores", "Universidade dos Açores"],
            "course_name": ["Ciclo Básico de Medicina", "Ciclo Básico de Medicina"],
        }
    )
    result = build_concordance_candidates(frame)
    assert result["source_pair_key"].tolist() == ["0160/8083", "0160/8083"]


def test_concordance_candidates_rejects_missing_schema_with_dataexcept() -> None:
    with pytest.raises(MissingColumnError):
        build_concordance_candidates(pd.DataFrame({"year": [2025]}))
