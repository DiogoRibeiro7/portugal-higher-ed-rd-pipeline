"""Build the v0.3.3 Study B matched-course demand/selectivity pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from pt_he_pipeline.study_b_course_pilot import (
    MatchedCoursePolicy,
    add_course_pilot_metrics,
    build_cross_section_associations,
    build_leave_one_year_out,
    build_nested_model_summary,
    build_year_summary,
    reconcile_overlapping_sources,
    summarise_leave_one_year_out,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INPUT = (
    ROOT
    / "data/curated/dges/course_9119_engineering_informatics_2018_2020_source_rows.csv"
)
SOURCE_MANIFEST = ROOT / "data/source_manifests/dges_study_b_course9119_pilot.csv"
STUDY_CONFIG = ROOT / "config/study_b_course9119_pilot.yml"
PACKAGE_SOURCE = ROOT / "src/pt_he_pipeline/study_b_course_pilot.py"
OUTPUT_DIR = ROOT / "results/study_b"
FIGURE_DIR = ROOT / "figures/study_b"


def _sha256(path: Path) -> str:
    """Return a SHA-256 digest for one file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a deterministic CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.10g")


def _plot_demand_grade(panel: pd.DataFrame, outcome: str, path: Path, title: str) -> None:
    """Plot demand pressure against one grade outcome by year."""

    figure, axis = plt.subplots(figsize=(7.2, 4.5))
    for year, subset in panel.groupby("year", sort=True):
        axis.scatter(
            subset["applicants_per_vacancy"],
            subset[outcome],
            label=str(year),
            alpha=0.85,
        )
    axis.set_xscale("log")
    axis.set_xlabel("Applicants per vacancy (log scale)")
    axis.set_ylabel("Grade (0-200)")
    axis.set_title(title)
    axis.legend(title="Year")
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)


def _write_findings(
    panel: pd.DataFrame,
    year_summary: pd.DataFrame,
    associations: pd.DataFrame,
    models: pd.DataFrame,
    loyo_summary: pd.DataFrame,
    path: Path,
) -> None:
    """Write a mechanically derived interpretation note for the pilot."""

    association_index = associations.set_index(
        ["year", "outcome", "demand_variable"]
    )
    model_index = models.set_index(["outcome", "model"])
    loyo_index = loyo_summary.set_index(["outcome", "model"])

    cutoff = "last_placed_general_contingent_grade"
    mean_grade = "mean_application_grade_placed"
    demand = "applicants_per_vacancy"

    cutoff_r2 = [
        float(association_index.loc[(year, cutoff, demand), "r_squared"])
        for year in (2018, 2019, 2020)
    ]
    mean_r2 = [
        float(association_index.loc[(year, mean_grade, demand), "r_squared"])
        for year in (2018, 2019, 2020)
    ]
    pooled_cutoff_increment = float(
        model_index.loc[(cutoff, "year_plus_demand"), "incremental_r_squared_vs_structure"]
    )
    fe_cutoff_increment = float(
        model_index.loc[
            (cutoff, "institution_year_plus_demand"),
            "incremental_r_squared_vs_structure",
        ]
    )
    pooled_mean_increment = float(
        model_index.loc[
            (mean_grade, "year_plus_demand"), "incremental_r_squared_vs_structure"
        ]
    )
    fe_mean_increment = float(
        model_index.loc[
            (mean_grade, "institution_year_plus_demand"),
            "incremental_r_squared_vs_structure",
        ]
    )

    cutoff_loyo_without = float(
        loyo_index.loc[(cutoff, "institution_year"), "mean_rmse"]
    )
    cutoff_loyo_with = float(
        loyo_index.loc[(cutoff, "institution_year_plus_demand"), "mean_rmse"]
    )
    mean_loyo_without = float(
        loyo_index.loc[(mean_grade, "institution_year"), "mean_rmse"]
    )
    mean_loyo_with = float(
        loyo_index.loc[(mean_grade, "institution_year_plus_demand"), "mean_rmse"]
    )

    lines = [
        "# Study B matched-course pilot findings",
        "",
        "## Scope",
        "",
        "The pilot holds the exact DGES programme code 9119 (Engenharia Informática,",
        "Licenciatura) fixed across 23 institutions in 2018, 2019 and 2020. This produces",
        f"a balanced {len(panel)}-row institution-year panel. It is a pipeline and",
        "identification pilot, not an estimate for all Portuguese programmes.",
        "",
        "The 2019 course observations appear in both consecutive official comparative",
        "tables. All registered counts and grade measures agree exactly across the two",
        "sources before the canonical 2019 rows are selected.",
        "",
        "## Demand and grades",
        "",
        "Within each year, a one-predictor log-demand model using applicants per vacancy",
        "accounts for the following shares of cross-institution grade variation:",
        "",
        f"- cut-off grade: {cutoff_r2[0]:.3f} in 2018, {cutoff_r2[1]:.3f} in 2019 and "
        f"{cutoff_r2[2]:.3f} in 2020;",
        f"- mean application grade of placed candidates: {mean_r2[0]:.3f} in 2018, "
        f"{mean_r2[1]:.3f} in 2019 and {mean_r2[2]:.3f} in 2020.",
        "",
        "The association is therefore strong in this matched course, but it is not a",
        "near-complete deterministic explanation in every year.",
        "",
        "## Nested descriptions",
        "",
        "Relative to a linear calendar-year description, adding log applicants per vacancy",
        f"raises R-squared by {pooled_cutoff_increment:.3f} for the cut-off and by "
        f"{pooled_mean_increment:.3f} for the mean placed grade.",
        "",
        "Institution fixed effects absorb most persistent cross-institution differences.",
        "Against that richer structural baseline, adding contemporaneous demand raises",
        f"R-squared by {fe_cutoff_increment:.3f} for the cut-off and by "
        f"{fe_mean_increment:.3f} for the mean placed grade.",
        "",
        "This is not a contradiction: cross-sectional demand differences can be highly",
        "informative while persistent institution characteristics explain much of the same",
        "between-institution variation.",
        "",
        "## Leave-one-year-out prediction",
        "",
        "For the institution-plus-year specification, adding demand changes mean held-out",
        f"cut-off RMSE from {cutoff_loyo_without:.2f} to {cutoff_loyo_with:.2f} grade points",
        f"and mean-grade RMSE from {mean_loyo_without:.2f} to {mean_loyo_with:.2f} points.",
        "Demand therefore adds predictive information in this three-year pilot as well as",
        "cross-sectional explanatory information.",
        "",
        "## Interpretation boundary",
        "",
        "The pilot does not test rankings, does not establish causality, and does not yet",
        "support a statement about all universities or all courses. It shows that the DGES",
        "comparative-course family can recover vacancies, total applicants, first-choice",
        "applicants, placements and grade outcomes in a directly matched design. The next",
        "step is to scale the same contract to many programmes and years before adjudicating",
        "the registered Study B proposition.",
        "",
        "Year-level descriptive means are retained in `course9119_year_summary.csv`; the",
        "2020 increase in average demand and grades coincides with pandemic-era schooling and",
        "assessment conditions and is not interpreted as a causal year effect.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _receipt_payload(outputs: list[Path]) -> dict[str, Any]:
    """Build a content-addressed receipt for the matched-course pilot."""

    inputs = [
        SOURCE_INPUT,
        SOURCE_MANIFEST,
        STUDY_CONFIG,
        ROOT / "config/study.yml",
        PACKAGE_SOURCE,
        ROOT / "tests/test_study_b_course_pilot.py",
        ROOT / "tests/test_study_b_course_pilot_release_data.py",
        Path(__file__).resolve(),
    ]
    payload: dict[str, Any] = {
        "analysis": "study_b_matched_course_9119_pilot",
        "version": "0.3.3",
        "programme_code": "9119",
        "years": [2018, 2019, 2020],
        "institutions_per_year": 23,
        "source_rows": 92,
        "canonical_rows": 69,
        "overlap_year": 2019,
        "provider_bytes_bundled": False,
        "curation_status": "transcribed_from_official_published_comparative_tables",
        "sampling_inference": False,
        "causal_interpretation": False,
        "inputs": {str(file.relative_to(ROOT)): _sha256(file) for file in inputs},
        "outputs": {str(file.relative_to(ROOT)): _sha256(file) for file in outputs},
    }
    serialised = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload["receipt_sha256"] = hashlib.sha256(serialised.encode("utf-8")).hexdigest()
    return payload


def main() -> None:
    """Build all v0.3.3 matched-course pilot outputs."""

    source_rows = pd.read_csv(
        SOURCE_INPUT,
        dtype={"programme_code": str, "institution_code": str},
    )
    policy = MatchedCoursePolicy()
    canonical, reconciliation = reconcile_overlapping_sources(source_rows, policy=policy)
    panel = add_course_pilot_metrics(canonical)
    year_summary = build_year_summary(panel)
    associations = build_cross_section_associations(panel)
    models = build_nested_model_summary(panel)
    loyo = build_leave_one_year_out(panel)
    loyo_summary = summarise_leave_one_year_out(loyo)

    paths = {
        "panel": OUTPUT_DIR / "course9119_panel.csv",
        "reconciliation": OUTPUT_DIR / "course9119_source_reconciliation.csv",
        "year_summary": OUTPUT_DIR / "course9119_year_summary.csv",
        "associations": OUTPUT_DIR / "course9119_cross_section_associations.csv",
        "models": OUTPUT_DIR / "course9119_nested_models.csv",
        "loyo": OUTPUT_DIR / "course9119_leave_one_year_out.csv",
        "loyo_summary": OUTPUT_DIR / "course9119_leave_one_year_out_summary.csv",
        "findings": OUTPUT_DIR / "course9119_findings.md",
    }
    _write_csv(panel, paths["panel"])
    _write_csv(reconciliation, paths["reconciliation"])
    _write_csv(year_summary, paths["year_summary"])
    _write_csv(associations, paths["associations"])
    _write_csv(models, paths["models"])
    _write_csv(loyo, paths["loyo"])
    _write_csv(loyo_summary, paths["loyo_summary"])
    _write_findings(panel, year_summary, associations, models, loyo_summary, paths["findings"])

    _plot_demand_grade(
        panel,
        "last_placed_general_contingent_grade",
        FIGURE_DIR / "course9119_demand_vs_cutoff.png",
        "Engineering Informatics 9119: demand pressure and cut-off grade",
    )
    _plot_demand_grade(
        panel,
        "mean_application_grade_placed",
        FIGURE_DIR / "course9119_demand_vs_mean_grade.png",
        "Engineering Informatics 9119: demand pressure and mean placed grade",
    )

    receipt_inputs = list(paths.values())
    receipt = _receipt_payload(receipt_inputs)
    receipt_path = OUTPUT_DIR / "course9119_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    model_index = models.set_index(["outcome", "model"])
    cutoff = model_index.loc[
        ("last_placed_general_contingent_grade", "year_plus_demand")
    ]
    print("Built Study B matched-course pilot")
    print(f"Source rows: {len(source_rows)}; canonical rows: {len(panel)}")
    print(f"Year + demand cut-off R-squared: {float(cutoff['r_squared']):.3f}")
    print(f"Receipt: {receipt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
