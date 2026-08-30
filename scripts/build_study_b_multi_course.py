"""Build the registered Study B multi-course evidence layer.

The builder is deliberately fail-closed. It never infers programme identities,
relaxes the registered coverage gate, or imputes missing grade observations.
Curated programme shards are concatenated only after every registered source
file is present.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

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
DEFAULT_CONFIG = ROOT / "config" / "study_b_multi_course.yml"
DEFAULT_SOURCE = ROOT / "data" / "curated" / "dges" / "study_b_multi_course_source_rows.csv"
DEFAULT_RESULTS = ROOT / "results" / "study_b"
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


def _load_config(path: Path) -> dict[str, Any]:
    """Load and minimally validate the frozen Study B configuration."""

    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise TypeError("Study B multi-course configuration must be a mapping")
    return config


def _registry(config: dict[str, Any]) -> tuple[RegisteredProgramme, ...]:
    """Build the exact programme registry from the frozen configuration."""

    selection = config.get("selection")
    if not isinstance(selection, dict):
        raise ValueError("configuration is missing selection")
    raw_programmes = selection.get("registered_programmes")
    if not isinstance(raw_programmes, list) or not raw_programmes:
        raise ValueError("configuration has no registered programmes")

    programmes: list[RegisteredProgramme] = []
    for item in raw_programmes:
        if not isinstance(item, dict):
            raise TypeError("registered programme entries must be mappings")
        programmes.append(
            RegisteredProgramme(
                code=str(item["code"]),
                name=str(item["name"]),
                degree=str(item["degree"]),
            )
        )
    return tuple(programmes)


def _policy(config: dict[str, Any]) -> MultiCoursePolicy:
    """Construct the frozen coverage policy from the configuration."""

    scope = config.get("scope")
    if not isinstance(scope, dict):
        raise ValueError("configuration is missing scope")
    years = scope.get("years")
    if not isinstance(years, list) or not years:
        raise ValueError("configuration scope must contain years")
    parsed_years = tuple(int(year) for year in years)
    expected = tuple(range(min(parsed_years), max(parsed_years) + 1))
    if parsed_years != expected:
        raise ValueError("registered Study B years must be consecutive and ordered")

    return MultiCoursePolicy(
        first_year=expected[0],
        last_year=expected[-1],
        overlap_year=int(scope["overlap_year"]),
        min_stable_institutions=int(scope["minimum_stable_institutions_per_programme"]),
    )


def _load_source(source_path: Path) -> pd.DataFrame:
    """Load a consolidated source table or the complete registered shard set."""

    dtype = {"programme_code": str, "institution_code": str}
    if source_path.exists():
        return pd.read_csv(source_path, dtype=dtype)

    source_dir = source_path.parent
    paths = tuple(source_dir / name for name in SOURCE_SHARDS)
    missing = [path.name for path in paths if not path.exists()]
    if missing:
        names = ", ".join(missing)
        raise FileNotFoundError(f"registered multi-course source shards are missing: {names}")

    frames = [pd.read_csv(path, dtype=dtype) for path in paths]
    return pd.concat(frames, ignore_index=True)


def build(*, config_path: Path, source_path: Path, results_dir: Path) -> None:
    """Validate curated source rows and write deterministic model artefacts."""

    config = _load_config(config_path)
    programmes = _registry(config)
    policy = _policy(config)
    source = _load_source(source_path)

    canonical, reconciliation = reconcile_sources(
        source,
        programmes=programmes,
        policy=policy,
    )
    stable, coverage = build_stable_panel(
        canonical,
        reconciliation,
        programmes=programmes,
        policy=policy,
    )
    stable = add_metrics(stable, policy=policy)
    model_panel, attrition = build_model_panel(stable, policy=policy)
    associations = programme_year_associations(model_panel)
    summary = summarise_associations(associations)

    results_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "multi_course_reconciliation.csv": reconciliation,
        "multi_course_coverage.csv": coverage,
        "multi_course_stable_panel.csv": stable,
        "multi_course_model_attrition.csv": attrition,
        "multi_course_model_panel.csv": model_panel,
        "multi_course_programme_year_associations.csv": associations,
        "multi_course_association_summary.csv": summary,
    }
    for name, frame in outputs.items():
        frame.to_csv(results_dir / name, index=False)


def main() -> None:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    args = parser.parse_args()
    build(config_path=args.config, source_path=args.source, results_dir=args.results_dir)


if __name__ == "__main__":
    main()
