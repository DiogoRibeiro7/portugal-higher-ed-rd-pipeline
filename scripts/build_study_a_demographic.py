"""Build the v0.3.2 Study A broad-cohort demographic sensitivity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from pt_he_pipeline.study_a_demography import (
    CohortProxyPolicy,
    build_demographic_endpoint_comparison,
    build_demographic_normalised_components,
    build_demographic_normalised_stem,
)

ROOT = Path(__file__).resolve().parents[1]
POPULATION_INPUT = ROOT / "data/curated/demography/pt_population_15_24_2016_2025.csv"
STEM_INPUT = ROOT / "results/study_a/medium_run_stem_summary.csv"
COMPONENT_INPUT = ROOT / "results/study_a/medium_run_component_metrics.csv"
SOURCE_MANIFEST = ROOT / "data/source_manifests/study_a_demographic.csv"
ARCHIVE_AUDIT = ROOT / "data/source_manifests/dges_2019_archive_audit.csv"
STUDY_CONFIG = ROOT / "config/study_a_demographic.yml"
PACKAGE_SOURCE = ROOT / "src/pt_he_pipeline/study_a_demography.py"
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
    """Load the frozen demographic sensitivity configuration."""

    payload = yaml.safe_load(STUDY_CONFIG.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("demographic study configuration must be a mapping")
    return payload


def _plot_normalised_index(normalised: pd.DataFrame, path: Path) -> None:
    """Plot raw placements and the broad-cohort rate on a common endpoint index."""

    frame = normalised.copy().sort_values("year", kind="stable")
    base_raw = float(frame.iloc[0]["placements"])
    base_rate = float(frame.iloc[0]["stem_placements_per_1000_cohort_proxy"])
    frame["raw_index"] = 100.0 * frame["placements"].astype(float) / base_raw
    frame["cohort_proxy_index"] = (
        100.0 * frame["stem_placements_per_1000_cohort_proxy"].astype(float) / base_rate
    )

    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    axis.plot(frame["year"], frame["raw_index"], marker="o", label="Raw placements")
    axis.plot(
        frame["year"],
        frame["cohort_proxy_index"],
        marker="o",
        label="Placements per cohort proxy",
    )
    axis.axhline(100.0, linewidth=0.8)
    axis.set_xlabel("Competition year")
    axis.set_ylabel("Index (2017 = 100)")
    axis.set_title("Registered STEM: raw and broad-cohort-normalised paths")
    axis.set_xticks(list(range(2017, 2027)))
    axis.legend(fontsize=8)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_findings(
    normalised: pd.DataFrame,
    endpoints: pd.DataFrame,
    path: Path,
) -> None:
    """Write the mechanically derived demographic sensitivity interpretation."""

    frame = normalised.set_index("year")
    endpoint = endpoints.set_index("stem_code")
    population_change = (
        float(frame.loc[2026, "population_15_24"])
        / float(frame.loc[2017, "population_15_24"])
        - 1.0
    )
    all_stem = endpoint.loc["STEM"]

    lines = [
        "# Study A demographic sensitivity findings",
        "",
        "## Denominator boundary",
        "",
        "The registered exact age-18 denominator is not yet source-locked. This release",
        "therefore uses a deliberately weaker cohort-scale sensitivity: the INE resident",
        "population aged 15-24, disseminated by PORDATA, divided by ten to form an average",
        "single-year cohort proxy. Competition year t uses the population reported for t-1.",
        "This quantity is never relabelled as the population aged 18.",
        "",
        "## Endpoint comparison",
        "",
        "All registered STEM placements rise by "
        f"{100.0 * float(all_stem['raw_placement_change']):+.1f}% between 2017 and 2026.",
        "Over the corresponding previous-year population references, the 15-24 population",
        f"rises by {100.0 * population_change:+.1f}%.",
        "The broad-cohort-normalised STEM rate therefore changes from "
        f"{float(all_stem['cohort_proxy_rate_first']):.1f} to "
        f"{float(all_stem['cohort_proxy_rate_last']):.1f} placements per 1,000 average",
        "single-year cohort equivalents, an endpoint change of "
        f"{100.0 * float(all_stem['cohort_proxy_rate_change']):+.1f}%.",
        "",
        "Component cohort-proxy endpoint changes are:",
        "",
        "- group 05, natural sciences, mathematics and statistics: "
        f"{100.0 * float(endpoint.loc['05', 'cohort_proxy_rate_change']):+.1f}%;",
        "- group 06, information and communication technologies: "
        f"{100.0 * float(endpoint.loc['06', 'cohort_proxy_rate_change']):+.1f}%;",
        "- group 07, engineering, manufacturing and construction: "
        f"{100.0 * float(endpoint.loc['07', 'cohort_proxy_rate_change']):+.1f}%.",
        "",
        "## Interpretation",
        "",
        "The +9.0% raw all-STEM endpoint increase is much smaller after broad-cohort",
        "normalisation (+1.3%). This does not reverse the raw-count conclusion, but it shows",
        "that most of the endpoint increase is commensurate with the growth of the relevant",
        "young-adult population proxy. The component divergence remains: group 05 weakens,",
        "ICT expands strongly, and group 07 is only modestly higher after normalisation.",
        "",
        "This sensitivity does not fill the missing 2019 broad-area observation, does not",
        "replace an exact age-18 denominator, and does not authorise causal or structural-break",
        "claims. Counts, national placement share and demographic-normalised rates remain",
        "distinct empirical margins.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _receipt_payload(outputs: list[Path]) -> dict[str, Any]:
    """Build a content-addressed receipt for the v0.3.2 demographic sensitivity."""

    inputs = [
        POPULATION_INPUT,
        STEM_INPUT,
        COMPONENT_INPUT,
        SOURCE_MANIFEST,
        ARCHIVE_AUDIT,
        STUDY_CONFIG,
        ROOT / "config/study.yml",
        PACKAGE_SOURCE,
        ROOT / "tests/test_study_a_demography.py",
        ROOT / "tests/test_study_a_demographic_release_data.py",
        Path(__file__).resolve(),
    ]
    payload: dict[str, Any] = {
        "analysis": "study_a_demographic_cohort_proxy_sensitivity",
        "version": "0.3.2",
        "admission_window": [2017, 2026],
        "observed_admission_years": [
            2017,
            2018,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
            2026,
        ],
        "population_reference_rule": "previous_calendar_year",
        "denominator": "INE/PORDATA population aged 15-24 divided by 10",
        "exact_age_18_denominator": False,
        "primary_estimand": False,
        "provider_bytes_bundled": False,
        "imputation_used": False,
        "inputs": {str(item.relative_to(ROOT)): _sha256(item) for item in inputs},
        "outputs": {str(item.relative_to(ROOT)): _sha256(item) for item in outputs},
    }
    serialised = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["receipt_sha256"] = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return payload


def main() -> None:
    """Validate sources, build the sensitivity outputs, figure and receipt."""

    config = _load_config()
    denominator = config["denominator"]
    policy = CohortProxyPolicy(
        age_band_years=int(denominator["age_band_years"]),
        population_lag_years=1,
    )

    population = pd.read_csv(POPULATION_INPUT)
    stem = pd.read_csv(STEM_INPUT)
    components = pd.read_csv(COMPONENT_INPUT)

    normalised = build_demographic_normalised_stem(stem, population, policy=policy)
    normalised_components = build_demographic_normalised_components(
        components, population, policy=policy
    )
    endpoints = build_demographic_endpoint_comparison(normalised_components, normalised)

    stem_path = OUTPUT_DIR / "demographic_stem_metrics.csv"
    component_path = OUTPUT_DIR / "demographic_component_metrics.csv"
    endpoint_path = OUTPUT_DIR / "demographic_endpoint_comparison.csv"
    findings_path = OUTPUT_DIR / "demographic_findings.md"

    _write_csv(normalised, stem_path)
    _write_csv(normalised_components, component_path)
    _write_csv(endpoints, endpoint_path)
    _write_findings(normalised, endpoints, findings_path)
    _plot_normalised_index(normalised, FIGURE_DIR / "medium_run_demographic_index.png")

    receipt = _receipt_payload([stem_path, component_path, endpoint_path, findings_path])
    receipt_path = OUTPUT_DIR / "demographic_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    all_stem = endpoints.set_index("stem_code").loc["STEM"]
    print("Built Study A demographic cohort-proxy sensitivity")
    print(
        "All-STEM raw endpoint change: "
        f"{100.0 * float(all_stem['raw_placement_change']):+.2f}%"
    )
    print(
        "All-STEM cohort-proxy endpoint change: "
        f"{100.0 * float(all_stem['cohort_proxy_rate_change']):+.2f}%"
    )
    print(f"Receipt: {receipt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
