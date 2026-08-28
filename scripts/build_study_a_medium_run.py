"""Build the receipt-bound medium-run Study A broad-area outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from pt_he_pipeline.study_a import (
    build_endpoint_comparison,
    build_stem_component_metrics,
    build_stem_source_area_metrics,
    build_stem_summary,
    validate_study_a_area_panel,
)
from pt_he_pipeline.study_a_trends import build_medium_run_coverage, fit_medium_run_trends

ROOT = Path(__file__).resolve().parents[1]
AREA_INPUT = ROOT / "data/curated/dges/first_phase_area_2017_2026_observed.csv"
NATIONAL_INPUT = ROOT / "data/curated/dges/national_first_phase_2013_2026.csv"
SOURCE_MANIFEST = ROOT / "data/source_manifests/dges_study_a_medium_run.csv"
STUDY_CONFIG = ROOT / "config/study_a_medium_run.yml"
PACKAGE_SOURCE = ROOT / "src/pt_he_pipeline/study_a.py"
TREND_SOURCE = ROOT / "src/pt_he_pipeline/study_a_trends.py"
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


def _load_config() -> dict[str, Any]:
    """Load and validate the frozen medium-run configuration."""

    payload = yaml.safe_load(STUDY_CONFIG.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("medium-run study configuration must be a mapping")
    return payload


def _validate_source_coverage(
    area: pd.DataFrame,
    manifest: pd.DataFrame,
    expected_years: list[int],
) -> None:
    """Require the manifest and curated observations to agree exactly on source status."""

    required = {"year", "coverage_status", "source_table", "source_url"}
    missing_columns = sorted(required.difference(manifest.columns))
    if missing_columns:
        raise ValueError(f"medium-run source manifest is missing columns: {missing_columns}")

    manifest = manifest.copy()
    manifest["year"] = pd.to_numeric(manifest["year"], errors="raise").astype(int)
    if manifest["year"].duplicated().any():
        raise ValueError("medium-run source manifest contains duplicate years")
    if sorted(manifest["year"].tolist()) != expected_years:
        raise ValueError("medium-run source manifest must enumerate every expected year")

    observed_years = set(pd.to_numeric(area["year"], errors="raise").astype(int))
    locked_years = set(
        manifest.loc[manifest["coverage_status"] == "source_locked", "year"].astype(int)
    )
    if observed_years != locked_years:
        raise ValueError(
            "curated medium-run years must equal manifest source-locked years: "
            f"observed={sorted(observed_years)}, locked={sorted(locked_years)}"
        )

    pending = manifest.loc[manifest["coverage_status"] != "source_locked", "year"].astype(int)
    overlap = sorted(observed_years.intersection(set(pending.tolist())))
    if overlap:
        raise ValueError(f"non-source-locked years must not appear in curated data: {overlap}")


def _plot_component_index(
    components: pd.DataFrame,
    expected_years: list[int],
    path: Path,
) -> None:
    """Plot component placement indices, preserving the unobserved 2019 gap."""

    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    for component, subset in components.groupby("stem_component", sort=False):
        series = subset.set_index("year")["placements"].astype(float).reindex(expected_years)
        first_value = float(series.dropna().iloc[0])
        index = 100.0 * series / first_value
        axis.plot(index.index, index.values, marker="o", label=str(component))
    axis.axhline(100.0, linewidth=0.8)
    axis.set_xlabel("Competition year")
    axis.set_ylabel("Placement index (2017 = 100)")
    axis.set_title("STEM component placements: source-locked years")
    axis.set_xticks(expected_years)
    axis.legend(fontsize=8)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _plot_stem_total(
    summary: pd.DataFrame,
    expected_years: list[int],
    path: Path,
) -> None:
    """Plot all-STEM placements with the unobserved 2019 year shown as a gap."""

    series = summary.set_index("year")["placements"].astype(float).reindex(expected_years)
    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    axis.plot(series.index, series.values, marker="o")
    axis.set_xlabel("Competition year")
    axis.set_ylabel("First-phase placements")
    axis.set_title("Registered STEM placements, 2017-2026 observed vintages")
    axis.set_xticks(expected_years)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _plot_stem_share(
    summary: pd.DataFrame,
    expected_years: list[int],
    path: Path,
) -> None:
    """Plot all-STEM placement share with the unobserved 2019 year shown as a gap."""

    series = (
        100.0
        * summary.set_index("year")["placement_share"].astype(float).reindex(expected_years)
    )
    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    axis.plot(series.index, series.values, marker="o")
    axis.set_xlabel("Competition year")
    axis.set_ylabel("Share of all first-phase placements (%)")
    axis.set_title("Registered STEM placement share")
    axis.set_xticks(expected_years)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_findings(
    source_areas: pd.DataFrame,
    components: pd.DataFrame,
    summary: pd.DataFrame,
    endpoints: pd.DataFrame,
    trends: pd.DataFrame,
    coverage: pd.DataFrame,
    path: Path,
) -> None:
    """Write a concise mechanically derived medium-run result note."""

    endpoint = endpoints.set_index("stem_code")
    summary_by_year = summary.set_index("year")
    trend_index = trends.set_index(["specification", "series_code"])
    observed_years = coverage.loc[coverage["observed"], "year"].astype(int).tolist()
    missing_years = coverage.loc[~coverage["observed"], "year"].astype(int).tolist()

    placement_2017 = int(summary_by_year.loc[2017, "placements"])
    placement_2026 = int(summary_by_year.loc[2026, "placements"])
    share_2017 = 100.0 * float(summary_by_year.loc[2017, "placement_share"])
    share_2026 = 100.0 * float(summary_by_year.loc[2026, "placement_share"])

    all_stem_trend = trend_index.loc[("all_observed", "STEM")]
    sensitivity_trend = trend_index.loc[("exclude_pandemic_years", "STEM")]
    source_pivot = source_areas.pivot(
        index="canonical_area", columns="year", values="placements"
    )
    engineering_affine_change = (
        float(source_pivot.loc["Engenharia e Técnicas Afins", 2026])
        / float(source_pivot.loc["Engenharia e Técnicas Afins", 2017])
        - 1.0
    )

    lines = [
        "# Study A medium-run findings",
        "",
        "## Scope",
        "",
        "This release extends the official broad-area first-phase series to the source-locked",
        f"years {', '.join(str(year) for year in observed_years)}. The expected 2017-2026",
        "window still lacks a locked complete broad-area table for "
        f"{', '.join(str(year) for year in missing_years)}.",
        "No value is interpolated or reconstructed for that gap.",
        "",
        "The broad-area table reports first-choice candidates, not all programme applications.",
        "The full registered 1997-2026 programme-level Study A therefore remains pending.",
        "",
        "## Endpoint evidence",
        "",
        "Registered STEM placements rise from "
        f"{placement_2017:,} in 2017 to {placement_2026:,} in 2026,",
        f"an endpoint change of {100.0 * float(endpoint.loc['STEM', 'placement_change']):+.1f}%.",
        f"The corresponding placement share moves from {share_2017:.2f}% to {share_2026:.2f}%,",
        f"a change of {share_2026 - share_2017:+.2f} percentage points.",
        "",
        "Component endpoint changes are:",
        "",
        "- group 05, natural sciences, mathematics and statistics: "
        f"{100.0 * float(endpoint.loc['05', 'placement_change']):+.1f}%;",
        "- group 06, information and communication technologies: "
        f"{100.0 * float(endpoint.loc['06', 'placement_change']):+.1f}%;",
        "- group 07, engineering, manufacturing and construction: "
        f"{100.0 * float(endpoint.loc['07', 'placement_change']):+.1f}%.",
        "",
        "The source category `Engenharia e Técnicas Afins` changes by "
        f"{100.0 * engineering_affine_change:+.1f}%",
        "between the same endpoints.",
        "",
        "## Descriptive fitted path",
        "",
        f"Across all source-locked years, the all-STEM log-linear placement slope corresponds to",
        f"{float(all_stem_trend['placement_annual_trend_percent']):+.2f}% per calendar year",
        f"(descriptive R-squared {float(all_stem_trend['placement_r_squared']):.3f}). "
        "The placement-share",
        "line changes by "
        f"{float(all_stem_trend['placement_share_slope_pp_per_year']):+.3f} "
        "percentage points per year.",
        "",
        "The frozen sensitivity omitting 2020 and 2021 gives an all-STEM placement slope of",
        f"{float(sensitivity_trend['placement_annual_trend_percent']):+.2f}% per calendar "
        "year and a placement-share",
        "gradient of "
        f"{float(sensitivity_trend['placement_share_slope_pp_per_year']):+.3f} "
        "percentage points per year.",
        "",
        "These fitted lines are compact descriptions of administrative population counts. They are",
        "not sampling-inference estimates, causal effects, or structural-break tests.",
        "",
        "## Interpretation boundary",
        "",
        "The medium-run source-locked evidence does not support a simple claim that the absolute",
        "number of first-phase STEM placements has been falling continuously since 2017. It also",
        "does not settle the registered long-run thesis: the broad-area layer has a 2019 "
        "source gap,",
        "does not yet extend to 1997, and does not provide programme-level applicants per "
        "vacancy or",
        "demographic normalisation. Count trends and field shares also point to different "
        "margins and",
        "must be reported together.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _receipt_payload(outputs: list[Path]) -> dict[str, Any]:
    """Build a content-addressed receipt for the medium-run broad-area analysis."""

    inputs = [
        AREA_INPUT,
        NATIONAL_INPUT,
        SOURCE_MANIFEST,
        STUDY_CONFIG,
        ROOT / "config/study.yml",
        PACKAGE_SOURCE,
        TREND_SOURCE,
        ROOT / "tests/test_study_a.py",
        ROOT / "tests/test_study_a_release_data.py",
        ROOT / "tests/test_study_a_trends.py",
        ROOT / "tests/test_study_a_medium_run_release_data.py",
        Path(__file__).resolve(),
    ]
    payload: dict[str, Any] = {
        "analysis": "study_a_medium_run_broad_area",
        "version": "0.3.1",
        "expected_window": [2017, 2026],
        "observed_years": [2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
        "missing_source_years": [2019],
        "provider_bytes_bundled": False,
        "curation_status": "transcribed_from_official_published_aggregate_tables",
        "imputation_used": False,
        "inputs": {str(path.relative_to(ROOT)): _sha256(path) for path in inputs},
        "outputs": {str(path.relative_to(ROOT)): _sha256(path) for path in outputs},
    }
    serialised = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["receipt_sha256"] = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return payload


def main() -> None:
    """Validate inputs, build medium-run outputs, figures and a content receipt."""

    config = _load_config()
    expected_years = [int(year) for year in config["window"]["expected_years"]]
    excluded_years = [int(year) for year in config["sensitivity"]["exclude_years"]]

    area = pd.read_csv(AREA_INPUT)
    national = pd.read_csv(NATIONAL_INPUT)
    manifest = pd.read_csv(SOURCE_MANIFEST)
    _validate_source_coverage(area, manifest, expected_years)
    validate_study_a_area_panel(area, national)

    source_areas = build_stem_source_area_metrics(area, national)
    components = build_stem_component_metrics(area, national)
    summary = build_stem_summary(components)
    endpoints = build_endpoint_comparison(components, summary)
    coverage = build_medium_run_coverage(area["year"].astype(int), expected_years)

    trends_all = fit_medium_run_trends(
        components,
        summary,
        expected_years=expected_years,
        specification="all_observed",
    )
    trends_sensitivity = fit_medium_run_trends(
        components,
        summary,
        expected_years=expected_years,
        exclude_years=excluded_years,
        specification="exclude_pandemic_years",
    )
    trends = pd.concat([trends_all, trends_sensitivity], ignore_index=True)

    source_area_path = OUTPUT_DIR / "medium_run_source_area_metrics.csv"
    component_path = OUTPUT_DIR / "medium_run_component_metrics.csv"
    summary_path = OUTPUT_DIR / "medium_run_stem_summary.csv"
    endpoint_path = OUTPUT_DIR / "medium_run_endpoint_comparison.csv"
    trend_path = OUTPUT_DIR / "medium_run_trends.csv"
    coverage_path = OUTPUT_DIR / "medium_run_coverage.csv"
    findings_path = OUTPUT_DIR / "medium_run_findings.md"

    _write_csv(source_areas, source_area_path)
    _write_csv(components, component_path)
    _write_csv(summary, summary_path)
    _write_csv(endpoints, endpoint_path)
    _write_csv(trends, trend_path)
    _write_csv(coverage, coverage_path)
    _write_findings(source_areas, components, summary, endpoints, trends, coverage, findings_path)

    _plot_stem_total(summary, expected_years, FIGURE_DIR / "medium_run_stem_total.png")
    _plot_component_index(
        components,
        expected_years,
        FIGURE_DIR / "medium_run_component_index.png",
    )
    _plot_stem_share(summary, expected_years, FIGURE_DIR / "medium_run_stem_share.png")

    receipt_outputs = [
        source_area_path,
        component_path,
        summary_path,
        endpoint_path,
        trend_path,
        coverage_path,
        findings_path,
    ]
    receipt = _receipt_payload(receipt_outputs)
    receipt_path = OUTPUT_DIR / "medium_run_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(f"Validated {len(area):,} DGES broad-area rows")
    print(f"Source-locked years: {coverage.loc[coverage['observed'], 'year'].tolist()}")
    print(f"Missing source years: {coverage.loc[~coverage['observed'], 'year'].tolist()}")
    print(f"Wrote {len(source_areas):,} STEM source-area rows")
    print(f"Wrote {len(components):,} component-year rows")
    print(f"Wrote {len(trends):,} descriptive trend rows")
    print(f"Receipt: {receipt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
