from __future__ import annotations

import pandas as pd
import pytest

from pt_he_pipeline.study_a import (
    build_endpoint_comparison,
    build_stem_component_metrics,
    build_stem_source_area_metrics,
    build_stem_summary,
    canonicalise_source_area,
    validate_study_a_area_panel,
)


def _area_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    areas = [
        ("Ciências da Vida", 10, 8, 9, 1),
        ("Ciências Físicas", 10, 8, 9, 1),
        ("Matemática e Estatística", 10, 8, 9, 1),
        ("Informática", 10, 8, 8, 2),
        ("Engenharia e Técnicas Afins", 20, 15, 16, 4),
        ("Indústrias Transformadoras", 10, 4, 5, 5),
        ("Arquitetura e Construção", 10, 7, 6, 4),
        ("Artes", 20, 22, 18, 2),
    ]
    for year, multiplier in ((2023, 1), (2024, 2)):
        for area, vacancies, first_choice, placements, remaining in areas:
            rows.append(
                {
                    "year": year,
                    "area": area,
                    "vacancies": vacancies * multiplier,
                    "first_choice_applicants": first_choice * multiplier,
                    "placements": placements * multiplier,
                    "remaining_vacancies": remaining * multiplier,
                    "source_document": f"note_{year}.pdf",
                    "source_table": "Quadro V",
                }
            )
    return pd.DataFrame(rows)


def _national_frame() -> pd.DataFrame:
    area = _area_frame()
    totals = area.groupby("year", as_index=False).agg(
        vacancies=("vacancies", "sum"),
        candidates=("first_choice_applicants", "sum"),
        placements=("placements", "sum"),
    )
    return totals


def test_canonicalise_source_area_handles_spelling_vintage() -> None:
    assert canonicalise_source_area("Arquitectura e Construção") == "Arquitetura e Construção"
    assert canonicalise_source_area("Protecção do Ambiente") == "Proteção do Ambiente"


def test_validate_study_a_area_panel_reconciles_totals() -> None:
    validate_study_a_area_panel(_area_frame(), _national_frame())


def test_validate_study_a_area_panel_accepts_string_years() -> None:
    area = _area_frame()
    national = _national_frame()
    area["year"] = area["year"].astype(str)
    national["year"] = national["year"].astype(str)
    validate_study_a_area_panel(area, national)


def test_validate_study_a_area_panel_rejects_mismatched_total() -> None:
    national = _national_frame()
    national.loc[national["year"] == 2024, "placements"] += 1
    with pytest.raises(ValueError, match="do not reconcile"):
        validate_study_a_area_panel(_area_frame(), national)


def test_validate_study_a_area_panel_rejects_coverage_change() -> None:
    area = _area_frame()
    area = area.loc[~((area["year"] == 2024) & (area["area"] == "Artes"))].copy()
    national = area.groupby("year", as_index=False).agg(
        vacancies=("vacancies", "sum"),
        candidates=("first_choice_applicants", "sum"),
        placements=("placements", "sum"),
    )
    with pytest.raises(ValueError, match="coverage changed"):
        validate_study_a_area_panel(area, national)



def test_build_stem_source_area_metrics_retains_published_areas() -> None:
    result = build_stem_source_area_metrics(_area_frame(), _national_frame())
    assert result["canonical_area"].nunique() == 7
    assert set(result["stem_code"]) == {"05", "06", "07"}
    assert "Engenharia e Técnicas Afins" in set(result["canonical_area"])

def test_build_stem_component_metrics_keeps_components_separate() -> None:
    result = build_stem_component_metrics(_area_frame(), _national_frame())
    assert set(result["stem_code"]) == {"05", "06", "07"}
    year = result.loc[result["year"] == 2023].set_index("stem_code")
    assert int(year.loc["05", "placements"]) == 27
    assert int(year.loc["06", "placements"]) == 8
    assert int(year.loc["07", "placements"]) == 27
    assert float(year.loc["06", "occupancy_rate"]) == pytest.approx(0.8)


def test_stem_summary_and_endpoint_comparison() -> None:
    components = build_stem_component_metrics(_area_frame(), _national_frame())
    summary = build_stem_summary(components)
    endpoints = build_endpoint_comparison(components, summary)

    assert summary["placements"].tolist() == [62, 124]
    all_stem = endpoints.loc[endpoints["stem_code"] == "STEM"].iloc[0]
    assert int(all_stem["placements_first"]) == 62
    assert int(all_stem["placements_last"]) == 124
    assert float(all_stem["placement_change"]) == pytest.approx(1.0)


def test_validate_study_a_area_panel_accepts_registered_historical_table_number() -> None:
    area = _area_frame()
    area.loc[area["year"] == 2023, "source_table"] = "Quadro XII"
    validate_study_a_area_panel(area, _national_frame())


def test_validate_study_a_area_panel_rejects_unknown_table_number() -> None:
    area = _area_frame()
    area.loc[area["year"] == 2023, "source_table"] = "Quadro IX"
    with pytest.raises(ValueError, match="registered DGES broad-area table"):
        validate_study_a_area_panel(area, _national_frame())


def test_validate_study_a_area_panel_checks_remaining_vacancies_when_available() -> None:
    national = _national_frame()
    area = _area_frame()
    remaining = area.groupby("year")["remaining_vacancies"].sum()
    national["remaining_vacancies"] = national["year"].map(remaining)
    national.loc[national["year"] == 2024, "remaining_vacancies"] += 1

    with pytest.raises(ValueError, match="remaining_vacancies"):
        validate_study_a_area_panel(area, national)
