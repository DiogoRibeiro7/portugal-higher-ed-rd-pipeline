"""Build the frozen Study B 2018-2021 descriptive extension."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from pt_he_pipeline.study_b_multi_course import (
    MultiCoursePolicy,
    RegisteredProgramme,
    add_metrics,
    build_model_panel,
    build_stable_panel,
    programme_year_associations,
    reconcile_sources,
    summarise_associations,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "curated" / "dges"
RESULTS_DIR = ROOT / "results" / "study_b" / "2021_extension"
BASELINE_RESULTS = ROOT / "results" / "study_b" / "multi_course_programme_year_associations.csv"
CONFIG = ROOT / "config" / "study_b_multi_course_2021_extension.yml"
SOURCE_2021 = SOURCE_DIR / "study_b_multi_course_2021_source_rows.csv"
COVERAGE_GATE = RESULTS_DIR / "study_b_2018_2021_coverage_gate.csv"

SOURCE_SHARDS = (
    "course_9081_economics_2018_2020_source_rows.csv",
    "course_9119_engineering_informatics_2018_2020_source_rows.csv",
    "course_9147_management_2018_2020_source_rows_part1.csv",
    "course_9147_management_2018_2020_source_rows_part2a.csv",
    "course_9147_management_2018_2020_source_rows_part2b.csv",
    "course_9219_psychology_2018_2020_source_rows.csv",
    "course_9500_nursing_2018_2020_source_rows_part1.csv",
    "course_9500_nursing_2018_2020_source_rows_part2.csv",
    "course_9500_nursing_2018_2020_source_rows_part3.csv",
    "course_9500_nursing_2018_2020_source_rows_part4.csv",
)


def _registry() -> tuple[RegisteredProgramme, ...]:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    items = config["selection"]["registered_programmes"]
    return tuple(
        RegisteredProgramme(
            code=str(item["code"]),
            name=str(item["name"]),
            degree=str(item["degree"]),
        )
        for item in items
    )


def _base_source() -> pd.DataFrame:
    dtype = {"programme_code": str, "institution_code": str}
    frames = [pd.read_csv(SOURCE_DIR / name, dtype=dtype) for name in SOURCE_SHARDS]
    return pd.concat(frames, ignore_index=True)


def _four_year_units() -> set[tuple[str, str]]:
    gate = pd.read_csv(COVERAGE_GATE, dtype={"programme_code": str})
    required = {"programme_code", "stable_institution_codes", "gate_passed"}
    if not required.issubset(gate.columns):
        raise ValueError("four-year coverage gate is incomplete")
    if not gate["gate_passed"].astype(bool).all():
        raise ValueError("four-year coverage gate did not pass")
    units: set[tuple[str, str]] = set()
    for row in gate.itertuples(index=False):
        for institution in str(row.stable_institution_codes).split("|"):
            units.add((str(row.programme_code), institution.zfill(4)))
    return units


def build() -> dict[str, pd.DataFrame]:
    programmes = _registry()
    base_policy = MultiCoursePolicy(first_year=2018, last_year=2020, overlap_year=2019)
    extension_policy = MultiCoursePolicy(first_year=2018, last_year=2021, overlap_year=2020)

    canonical, reconciliation = reconcile_sources(
        _base_source(), programmes=programmes, policy=base_policy
    )
    stable_base, _ = build_stable_panel(
        canonical, reconciliation, programmes=programmes, policy=base_policy
    )

    dtype = {"programme_code": str, "institution_code": str}
    rows_2021 = pd.read_csv(SOURCE_2021, dtype=dtype)
    combined = pd.concat([stable_base, rows_2021], ignore_index=True, sort=False)

    units = _four_year_units()
    keys = list(zip(combined["programme_code"], combined["institution_code"], strict=False))
    stable = combined.loc[[key in units for key in keys]].copy()
    stable = stable.sort_values(["programme_code", "institution_code", "year"], kind="stable")
    stable = add_metrics(stable.reset_index(drop=True), policy=extension_policy)

    model_panel, attrition = build_model_panel(stable, policy=extension_policy)
    associations = programme_year_associations(model_panel)
    summary = summarise_associations(associations)

    baseline = pd.read_csv(BASELINE_RESULTS, dtype={"programme_code": str})
    old = associations.loc[associations["year"] <= 2020].reset_index(drop=True)
    baseline = baseline.reset_index(drop=True)
    compare_columns = [
        "programme_code",
        "year",
        "outcome",
        "n",
        "r_squared",
        "log_demand_coefficient",
    ]
    pd.testing.assert_frame_equal(
        old[compare_columns],
        baseline[compare_columns],
        check_exact=True,
        check_dtype=False,
    )

    return {
        "study_b_2018_2021_model_attrition.csv": attrition,
        "study_b_2018_2021_programme_year_associations.csv": associations,
        "study_b_2018_2021_association_summary.csv": summary,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in build().items():
        frame.to_csv(RESULTS_DIR / name, index=False)


if __name__ == "__main__":
    main()
