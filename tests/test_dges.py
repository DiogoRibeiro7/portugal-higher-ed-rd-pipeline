from __future__ import annotations

from pt_he_pipeline.dges import (
    annual_statistics_url,
    discover_documents_from_html,
    discover_pair_references_from_html,
    pair_statistics_index_url,
)


def test_annual_statistics_url() -> None:
    assert annual_statistics_url(2025).endswith("/statcol/2025/")


def test_pair_statistics_index_url() -> None:
    assert pair_statistics_index_url(2004, 1).endswith("/statce/col04f1/index.htm")
    assert pair_statistics_index_url(2025, 2).endswith("/statce/col25f2/index.htm")


def test_discover_documents_from_anchor_text() -> None:
    html = """
    <html><body>
      <a href="Mobilidade25.pdf">
        Distrito/GAES de candidatura e 1ª opção vs. distrito de colocação
      </a>
      <a href="StCEs25.pdf">Estatística por par estabelecimento/curso (todos os pares)</a>
      <a href="Notas25.pdf">Classificações dos últimos colocados pelo contingente geral</a>
      <a href="Resumo25.pdf">Resumo da colocação</a>
    </body></html>
    """
    found = discover_documents_from_html(
        html,
        base_url="https://www.dges.gov.pt/guias/pdfs/statcol/2025/",
    )
    assert found["mobility"].endswith("Mobilidade25.pdf")
    assert found["pair_statistics_all"].endswith("StCEs25.pdf")
    assert found["last_placed_grades"].endswith("Notas25.pdf")
    assert found["placement_summary"].endswith("Resumo25.pdf")


def test_discover_pair_references_from_html() -> None:
    html = """
    <html><body>
      <p>0140 Universidade dos Açores - Faculdade de Ciências Agrárias e do Ambiente</p>
      <a href="ec25_01408086.pdf">
        Medicina Veterinária (Preparatórios) [Prep. Mestrado Integrado]
      </a>
      <a href="ec25_01409022.pdf">Ciências Agrárias [Licenciatura]</a>
    </body></html>
    """
    rows = discover_pair_references_from_html(
        html,
        year=2025,
        phase=1,
        base_url="https://www.dges.gov.pt/guias/pdfs/statce/col25f1/index.htm",
    )
    assert len(rows) == 2
    assert rows[0].institution_id == "0140"
    assert rows[0].course_id == "8086"
    assert rows[0].course_name == "Medicina Veterinária (Preparatórios)"
    assert rows[0].degree == "Prep. Mestrado Integrado"
    assert "Universidade dos Açores" in rows[0].institution_name
