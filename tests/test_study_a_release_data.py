from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pt_he_pipeline.study_a import (
    build_endpoint_comparison,
    build_stem_component_metrics,
    build_stem_summary,
    validate_study_a_area_panel,
)

ROOT = Path(__file__).resolve().parents[1]
AREA_PATH = ROOT / "data/curated/dges/first_phase_area_2023_2026.csv"
NATIONAL_PATH = ROOT / "data/curated/dges/national_first_phase_2013_2026.csv"


def _release_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the committed recent-window Study A release inputs."""

    return pd.read_csv(AREA_PATH), pd.read_csv(NATIONAL_PATH)


def test_release_area_panel_reconciles_to_national_controls() -> None:
    area, national = _release_inputs()
    validate_study_a_area_panel(area, national)
    assert len(area) == 92
    assert area.groupby("year").size().to_dict() == {2023: 23, 2024: 23, 2025: 23, 2026: 23}


def test_release_stem_summary_matches_registered_counts() -> None:
    area, national = _release_inputs()
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components).set_index("year")

    assert int(summary.loc[2023, "placements"]) == 14984
    assert int(summary.loc[2025, "placements"]) == 13183
    assert int(summary.loc[2026, "placements"]) == 15181
    assert float(summary.loc[2026, "placement_share"]) == pytest.approx(0.3036746614)


def test_release_endpoint_result_preserves_component_heterogeneity() -> None:
    area, national = _release_inputs()
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components)
    endpoints = build_endpoint_comparison(components, summary).set_index("stem_code")

    assert float(endpoints.loc["05", "placement_change"]) == pytest.approx(-0.0440741736)
    assert float(endpoints.loc["06", "placement_change"]) == pytest.approx(-0.0932964755)
    assert float(endpoints.loc["07", "placement_change"]) == pytest.approx(0.0505297474)
    assert float(endpoints.loc["STEM", "placement_change"]) == pytest.approx(0.0131473572)
