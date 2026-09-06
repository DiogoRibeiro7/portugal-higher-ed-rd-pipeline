from pathlib import Path

import pandas as pd

from pt_he_pipeline.dgeec_cnaef import (
    normalise_course_classification_table,
    parse_course_classification_excel,
)


def test_normalise_course_classification_table_maps_official_fields() -> None:
    frame = pd.DataFrame(
        {
            "Código estabelecimento": ["0160"],
            "Código curso": ["9119"],
            "Nome curso": ["Engenharia Informática"],
            "Grau": ["Licenciatura"],
            "CITE-F 2013": ["0613"],
            "CNAEF": ["481"],
        }
    )

    result = normalise_course_classification_table(frame)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["institution_id"] == "0160"
    assert row["course_id"] == "9119"
    assert row["course_name"] == "Engenharia Informática"
    assert row["degree"] == "Licenciatura"
    assert row["citef_2013_code"] == "0613"
    assert row["cite_1997_code"] == "481"
    assert row["isced_f_2013_2digit"] == "06"


def test_normalise_course_classification_table_preserves_non_stem_rows() -> None:
    frame = pd.DataFrame(
        {
            "Código curso": ["9081", "9119"],
            "Nome curso": ["Economia", "Engenharia Informática"],
            "CITE-F/2013 - Código": ["0311", "0613"],
        }
    )

    result = normalise_course_classification_table(frame)

    assert result["isced_f_2013_2digit"].tolist() == ["03", "06"]


def test_parse_course_classification_excel_adds_sha256(tmp_path: Path) -> None:
    path = tmp_path / "dgeec.xlsx"
    pd.DataFrame(
        {
            "Código curso": [9119],
            "Nome curso": ["Engenharia Informática"],
            "CITE-F 2013": [613],
        }
    ).to_excel(path, index=False)

    result = parse_course_classification_excel(path)

    assert result.loc[0, "course_id"] == "9119"
    assert result.loc[0, "citef_2013_code"] == "613"
    assert len(result.loc[0, "classification_source_sha256"]) == 64


def test_missing_citef_2013_column_is_rejected() -> None:
    frame = pd.DataFrame({"Código curso": ["9119"], "Nome curso": ["Engenharia Informática"]})

    try:
        normalise_course_classification_table(frame)
    except ValueError as exc:
        assert "citef_2013_code" in str(exc)
    else:
        raise AssertionError("missing CITE-F/2013 column should fail")
