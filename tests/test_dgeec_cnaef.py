from pathlib import Path

import pandas as pd

from pt_he_pipeline.dgeec_cnaef import (
    course_ficha_url,
    normalise_course_classification_table,
    parse_course_classification_excel,
    parse_course_ficha_file,
    parse_course_ficha_html,
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


def _ficha_html() -> str:
    return """
    <html><body>
      <div>Curso</div><div>9119 - Engenharia Informática</div>
      <div>Diploma</div><div>L1 - Licenciatura 1.º ciclo</div>
      <div>Área CNAEF 2013</div>
      <div>Principal</div><div>0714 - Eletrónica e automação</div>
      <div>Secundária</div><div>0613 - Desenvolvimento e análise de software e aplicações informáticas</div>
      <div>Url Direto</div><div>https://cnaef.dgeec.medu.pt/?accao=Ficha&amp;cod=139119</div>
    </body></html>
    """


def test_course_ficha_url_uses_stable_version_prefix() -> None:
    assert course_ficha_url("9119") == "https://cnaef.dgeec.medu.pt/?accao=Ficha&cod=139119"
    assert course_ficha_url("9119", classification_version=1997).endswith("cod=979119")


def test_parse_course_ficha_html_maps_principal_and_secondary_citef_2013() -> None:
    result = parse_course_ficha_html(
        _ficha_html(),
        expected_course_id="9119",
        source_url=course_ficha_url("9119"),
    )

    assert result["course_id"] == "9119"
    assert result["course_name"] == "Engenharia Informática"
    assert result["degree"] == "Licenciatura 1.º ciclo"
    assert result["citef_2013_code"] == "0714"
    assert result["secondary_classification_codes"] == "0613"
    assert result["isced_f_2013_2digit"] == "07"
    assert result["classification_source_url"] == course_ficha_url("9119")


def test_parse_course_ficha_html_rejects_wrong_course() -> None:
    try:
        parse_course_ficha_html(_ficha_html(), expected_course_id="9081")
    except ValueError as exc:
        assert "course mismatch" in str(exc)
    else:
        raise AssertionError("mismatched ficha should fail")


def test_parse_course_ficha_html_requires_principal_classification() -> None:
    html = _ficha_html().replace(
        "<div>Principal</div><div>0714 - Eletrónica e automação</div>", ""
    )
    try:
        parse_course_ficha_html(html, expected_course_id="9119")
    except ValueError as exc:
        assert "principal classification" in str(exc)
    else:
        raise AssertionError("ficha without principal classification should fail")


def test_parse_course_ficha_file_adds_sha256(tmp_path: Path) -> None:
    path = tmp_path / "9119.html"
    path.write_text(_ficha_html(), encoding="utf-8")

    result = parse_course_ficha_file(path, expected_course_id="9119")

    assert len(str(result["classification_source_sha256"])) == 64
