from decimal import Decimal

from pt_he_pipeline.study_b_2021_source import parse_comparative_section


def test_parse_comparative_section_reads_both_years() -> None:
    section = """
3122 Instituto Politécnico de Portalegre - Escola Superior de Tecnologia e Gestão
%var.
36
32
101 21 36 20 117.5 129.7 124.4 132.5
85 19 34 18 114.2 127.5 118.4 132.4
-11 -16 -10 -6 -10 -3.3 -2.2
2020
2021
132.5
132.4
"""

    rows = parse_comparative_section(section, programme_code="9670")

    assert len(rows) == 2
    assert rows[0].year == 2020
    assert rows[0].values == (
        Decimal("36"),
        Decimal("101"),
        Decimal("21"),
        Decimal("36"),
        Decimal("20"),
        Decimal("117.5"),
        Decimal("129.7"),
        Decimal("124.4"),
        Decimal("132.5"),
    )
    assert rows[1].year == 2021
    assert rows[1].values[0] == Decimal("32")
    assert rows[1].values[-1] == Decimal("132.4")


def test_parse_comparative_section_exposes_prior_code_note() -> None:
    section = """
0507 Universidade de Coimbra - Faculdade de Psicologia e de Ciências da Educação
Código em 2020: 9555
%var.
50
50
200 100 50 30 150.0 155.0 154.0 156.0
220 110 50 35 151.0 156.0 155.0 157.0
0 +10 +10 0 +17 +1.0 +1.0
2020
2021
156.0
157.0
"""

    rows = parse_comparative_section(section, programme_code="9219")

    assert {row.prior_programme_code for row in rows} == {"9555"}
