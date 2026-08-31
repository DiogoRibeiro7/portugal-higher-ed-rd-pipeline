from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "data/source_manifests/study_c_raides_file_inventory.yml"
SUPPORTED_EXCEL_SUFFIXES = (".xlsx", ".xlsb")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalise_header(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def canonical_staging_stem(family: str, academic_year: str) -> str:
    """Return the repo-local handoff stem, not a guessed provider filename."""
    safe_year = academic_year.replace("/", "_")
    return f"{family}_{safe_year}"


def annual_slots(inventory: dict[str, Any]) -> list[dict[str, str]]:
    years = inventory["frozen_window"]["academic_years"]
    families = inventory["annual_publication_families"]
    expected = inventory["byte_level_validation"]["total_expected_annual_files"]

    slots: list[dict[str, str]] = []
    for family, spec in families.items():
        if spec["expected_files"] != len(years):
            raise ValueError(
                f"Family {family!r} expects {spec['expected_files']} files, "
                f"but frozen window contains {len(years)} years"
            )
        for academic_year in years:
            slots.append(
                {
                    "academic_year": academic_year,
                    "family": family,
                    "local_stem": canonical_staging_stem(family, academic_year),
                }
            )

    if len(slots) != expected:
        raise ValueError(f"Inventory resolves to {len(slots)} files; expected {expected}")
    return slots


def resolve_staged_file(input_dir: Path, stem: str) -> Path | None:
    matches = [input_dir / f"{stem}{suffix}" for suffix in SUPPORTED_EXCEL_SUFFIXES]
    present = [path for path in matches if path.exists()]
    if len(present) > 1:
        raise ValueError(f"Multiple staged files found for {stem}: {present}")
    return present[0] if present else None


def workbook_fingerprint(path: Path) -> dict[str, Any]:
    engine = "pyxlsb" if path.suffix.lower() == ".xlsb" else None
    book = pd.ExcelFile(path, engine=engine)
    sheets: dict[str, Any] = {}
    for sheet in book.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet, nrows=25, header=None, engine=engine)
        rows = []
        for _, row in frame.iterrows():
            vals = [normalise_header(v) for v in row.tolist()]
            if any(vals):
                rows.append(vals)
        sheets[sheet] = {
            "nonempty_preview_rows": rows,
            "preview_width": max((len(r) for r in rows), default=0),
        }
    return {"sheet_names": book.sheet_names, "sheets": sheets}


def validate(inventory_path: Path, input_dir: Path) -> dict[str, Any]:
    inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    slots = annual_slots(inventory)
    expected = inventory["byte_level_validation"]["total_expected_annual_files"]

    records = []
    missing = []
    for item in slots:
        path = resolve_staged_file(input_dir, item["local_stem"])
        if path is None:
            missing.append(
                {
                    "academic_year": item["academic_year"],
                    "family": item["family"],
                    "reason": "file_missing",
                    "canonical_staging_stem": item["local_stem"],
                    "accepted_suffixes": list(SUPPORTED_EXCEL_SUFFIXES),
                }
            )
            continue
        records.append(
            {
                "academic_year": item["academic_year"],
                "family": item["family"],
                "filename": path.name,
                "sha256": sha256(path),
                "fingerprint": workbook_fingerprint(path),
            }
        )

    if missing:
        return {
            "status": "blocked_missing_files",
            "expected_files": expected,
            "validated_files": len(records),
            "missing": missing,
            "records": records,
            "endpoint_schema_comparable": False,
            "full_window_schema_validated": False,
        }

    by_key = {(r["academic_year"], r["family"]): r for r in records}
    endpoint_equal: dict[str, bool] = {}
    first_year = inventory["frozen_window"]["first_academic_year"]
    last_year = inventory["frozen_window"]["last_academic_year"]
    for family in inventory["annual_publication_families"]:
        first = by_key[(first_year, family)]["fingerprint"]
        last = by_key[(last_year, family)]["fingerprint"]
        endpoint_equal[family] = first["sheet_names"] == last["sheet_names"]

    return {
        "status": "validated_bytes_pending_semantic_schema_review",
        "expected_files": expected,
        "validated_files": len(records),
        "missing": [],
        "records": records,
        "endpoint_sheet_names_equal": endpoint_equal,
        "endpoint_schema_comparable": all(endpoint_equal.values()),
        "full_window_schema_validated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.inventory, args.input_dir)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    if result["status"] == "blocked_missing_files":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
