"""Build the receipt-bound recent-window Study A outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from pt_he_pipeline.study_a import (
    build_endpoint_comparison,
    build_stem_component_metrics,
    build_stem_source_area_metrics,
    build_stem_summary,
    validate_study_a_area_panel,
)

ROOT = Path(__file__).resolve().parents[1]
AREA_INPUT = ROOT / "data/curated/dges/first_phase_area_2023_2026.csv"
NATIONAL_INPUT = ROOT / "data/curated/dges/national_first_phase_2013_2026.csv"
SOURCE_MANIFEST = ROOT / "data/source_manifests/dges_study_a_recent.csv"
STUDY_CONFIG = ROOT / "config/study.yml"
PACKAGE_SOURCE = ROOT / "src/pt_he_pipeline/study_a.py"
OUTPUT_DIR = ROOT / "results/study_a"
FIGURE_DIR = ROOT / "figures/study_a"


def _sha256(path: Path) -> str:
    """Return the lower-case SHA-256 digest for one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a deterministic UTF-8 CSV without an index."""

    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")


def _plot_stem_total(summary: pd.DataFrame, path: Path) -> None:
    """Plot the all-STEM first-phase placement count."""

    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    axis.plot(summary["year"], summary["placements"], marker="o")
    axis.set_xlabel("Competition year")
    axis.set_ylabel("First-phase placements")
    axis.set_title("Registered STEM placements, 2023-2026")
    axis.set_xticks(summary["year"].astype(int).tolist())
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _plot_component_index(components: pd.DataFrame, path: Path) -> None:
    """Plot component placement indices normalised to 2023 = 100."""

    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    for component, subset in components.groupby("stem_component", sort=False):
        ordered = subset.sort_values("year", kind="stable")
        base = float(ordered.iloc[0]["placements"])
        index = 100.0 * ordered["placements"].astype(float) / base
        axis.plot(ordered["year"], index, marker="o", label=str(component))
    axis.axhline(100.0, linewidth=0.8)
    axis.set_xlabel("Competition year")
    axis.set_ylabel("Placement index (2023 = 100)")
    axis.set_title("STEM component placement trajectories")
    axis.set_xticks(sorted(components["year"].astype(int).unique().tolist()))
    axis.legend(fontsize=8)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _plot_stem_share(summary: pd.DataFrame, path: Path) -> None:
    """Plot the registered STEM share of all first-phase placements."""

    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    share_percent = 100.0 * summary["placement_share"]
    axis.plot(summary["year"], share_percent, marker="o")
    axis.set_xlabel("Competition year")
    axis.set_ylabel("Share of all first-phase placements (%)")
    axis.set_title("Registered STEM placement share, 2023-2026")
    axis.set_xticks(summary["year"].astype(int).tolist())
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_findings(
    source_areas: pd.DataFrame,
    components: pd.DataFrame,
    summary: pd.DataFrame,
    endpoints: pd.DataFrame,
    path: Path,
) -> None:
    """Write a concise, mechanically derived recent-window result note."""

    summary_by_year = summary.set_index("year")
    endpoint = endpoints.set_index("stem_code")
    placement_2023 = int(summary_by_year.loc[2023, "placements"])
    placement_2024 = int(summary_by_year.loc[2024, "placements"])
    placement_2025 = int(summary_by_year.loc[2025, "placements"])
    placement_2026 = int(summary_by_year.loc[2026, "placements"])
    share_2023 = 100.0 * float(summary_by_year.loc[2023, "placement_share"])
    share_2026 = 100.0 * float(summary_by_year.loc[2026, "placement_share"])
    occupancy_2025 = 100.0 * float(summary_by_year.loc[2025, "occupancy_rate"])
    occupancy_2026 = 100.0 * float(summary_by_year.loc[2026, "occupancy_rate"])

    rows = components.loc[
        components["year"].isin([2024, 2025, 2026]),
        ["year", "stem_code", "placements"],
    ]
    pivot = rows.pivot(index="stem_code", columns="year", values="placements")
    source_pivot = source_areas.pivot(
        index="canonical_area", columns="year", values="placements"
    )
    engineering_change = (
        float(source_pivot.loc["Engenharia e Técnicas Afins", 2026])
        / float(source_pivot.loc["Engenharia e Técnicas Afins", 2023])
        - 1.0
    )
    life_science_change = (
        float(source_pivot.loc["Ciências da Vida", 2026])
        / float(source_pivot.loc["Ciências da Vida", 2023])
        - 1.0
    )
    physical_science_change = (
        float(source_pivot.loc["Ciências Físicas", 2026])
        / float(source_pivot.loc["Ciências Físicas", 2023])
        - 1.0
    )
    maths_change = (
        float(source_pivot.loc["Matemática e Estatística", 2026])
        / float(source_pivot.loc["Matemática e Estatística", 2023])
        - 1.0
    )
    group_05_endpoint = 100.0 * float(endpoint.loc["05", "placement_change"])
    group_06_endpoint = 100.0 * float(endpoint.loc["06", "placement_change"])
    group_07_endpoint = 100.0 * float(endpoint.loc["07", "placement_change"])
    group_05_2025 = 100.0 * (
        float(pivot.loc["05", 2025]) / float(pivot.loc["05", 2024]) - 1.0
    )
    group_06_2025 = 100.0 * (
        float(pivot.loc["06", 2025]) / float(pivot.loc["06", 2024]) - 1.0
    )
    group_07_2025 = 100.0 * (
        float(pivot.loc["07", 2025]) / float(pivot.loc["07", 2024]) - 1.0
    )

    text = f"""# Study A recent-window findings

## Scope

This result uses the official DGES first-phase **Quadro V** broad-area tables for
2023-2026. It is a complete-population description of the published CNA first-phase
counts within this window, not a sample estimate. It is **not** yet the registered
long-run 1997-2026 programme-level analysis and contains no demographic normalisation.

The compact table reports first-choice candidates by broad area. It does not report
all applications by area, so this release uses **first-choice pressure** rather than
substituting it for applicants per vacancy.

## Registered STEM aggregate

First-phase placements in the registered STEM grouping were:

- 2023: {placement_2023:,}
- 2024: {placement_2024:,}
- 2025: {placement_2025:,}
- 2026: {placement_2026:,}

The 2025 fall was followed by a 2026 rebound. The 2026 aggregate was
{100.0 * float(endpoint.loc['STEM', 'placement_change']):+.1f}% relative to 2023.
Its share of all first-phase placements was {share_2023:.2f}% in 2023 and
{share_2026:.2f}% in 2026. Aggregate occupancy fell to {occupancy_2025:.1f}% in
2025 and recovered to {occupancy_2026:.1f}% in 2026.

## Components

Relative to 2023, 2026 placements were:

- natural sciences, mathematics and statistics: {group_05_endpoint:+.1f}%;
- information and communication technologies: {group_06_endpoint:+.1f}%;
- engineering, manufacturing and construction: {group_07_endpoint:+.1f}%.

The year-to-year break is visible in every component. From 2024 to 2025,
placements changed by {group_05_2025:+.1f}% in group 05, {group_06_2025:+.1f}%
in group 06, and {group_07_2025:+.1f}%
in group 07. All three then rose in 2026.

The source categories are heterogeneous too. Between 2023 and 2026,
`Engenharia e Técnicas Afins` changed by {100.0 * engineering_change:+.1f}%,
`Ciências da Vida` by {100.0 * life_science_change:+.1f}%, `Ciências Físicas`
by {100.0 * physical_science_change:+.1f}%, and `Matemática e Estatística` by
{100.0 * maths_change:+.1f}%. This is why the release preserves the seven source
areas beneath the three registered components.

## Interpretation boundary

These four years do not identify a sustained long-run trend. They do show that the
recent pattern is not well represented as one uninterrupted aggregate decline:
2025 is a sharp trough, while 2026 recovers strongly. At the same time, the endpoint
comparison is heterogeneous: science and ICT remain below their 2023 placement
counts, whereas engineering/manufacturing/construction is above its 2023 count.

The next Study A step remains the full historical programme-level panel, field
crosswalk validation, demographic denominators and formal long-run trend/break
analysis. No causal interpretation is attached to the compact-table movements.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _receipt_payload(outputs: list[Path]) -> dict[str, Any]:
    """Build a content-addressed receipt for the curated recent-window analysis."""

    inputs = [
        AREA_INPUT,
        NATIONAL_INPUT,
        SOURCE_MANIFEST,
        STUDY_CONFIG,
        PACKAGE_SOURCE,
        ROOT / "tests/test_study_a.py",
        ROOT / "tests/test_study_a_release_data.py",
        Path(__file__).resolve(),
    ]
    payload: dict[str, Any] = {
        "analysis": "study_a_recent_window",
        "version": "0.3.0",
        "window": [2023, 2026],
        "provider_bytes_bundled": False,
        "curation_status": "transcribed_from_official_published_aggregate_tables",
        "inputs": {str(path.relative_to(ROOT)): _sha256(path) for path in inputs},
        "outputs": {str(path.relative_to(ROOT)): _sha256(path) for path in outputs},
    }
    serialised = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["receipt_sha256"] = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return payload


def main() -> None:
    """Validate inputs, build Study A outputs, figures and a content receipt."""

    area = pd.read_csv(AREA_INPUT)
    national = pd.read_csv(NATIONAL_INPUT)
    validate_study_a_area_panel(area, national)

    source_areas = build_stem_source_area_metrics(area, national)
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components)
    endpoints = build_endpoint_comparison(components, summary)

    source_area_path = OUTPUT_DIR / "recent_window_source_area_metrics.csv"
    component_path = OUTPUT_DIR / "recent_window_component_metrics.csv"
    summary_path = OUTPUT_DIR / "recent_window_stem_summary.csv"
    endpoint_path = OUTPUT_DIR / "recent_window_endpoint_comparison.csv"
    findings_path = OUTPUT_DIR / "recent_window_findings.md"

    _write_csv(source_areas, source_area_path)
    _write_csv(components, component_path)
    _write_csv(summary, summary_path)
    _write_csv(endpoints, endpoint_path)
    _write_findings(source_areas, components, summary, endpoints, findings_path)

    _plot_stem_total(summary, FIGURE_DIR / "stem_total_placements.png")
    _plot_component_index(components, FIGURE_DIR / "stem_component_index.png")
    _plot_stem_share(summary, FIGURE_DIR / "stem_placement_share.png")

    receipt_outputs = [
        source_area_path,
        component_path,
        summary_path,
        endpoint_path,
        findings_path,
    ]
    receipt = _receipt_payload(receipt_outputs)
    receipt_path = OUTPUT_DIR / "recent_window_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Validated {len(area):,} DGES broad-area rows")
    print(f"Wrote {len(source_areas):,} STEM source-area rows")
    print(f"Wrote {len(components):,} component-year rows")
    print(f"Wrote {len(summary):,} all-STEM annual rows")
    print(f"Receipt: {receipt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
