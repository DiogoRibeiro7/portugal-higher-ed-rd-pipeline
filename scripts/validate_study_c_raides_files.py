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


def workbook_fingerprint(path: Path) -> dict[str, Any]:
    book = pd.ExcelFile(path)
    sheets: dict[str, Any] = {}
    for sheet in book.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet, nrows=25, header=None)
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
    annual = inventory["annual_files"]
    expected = inventory["expected_annual_file_count"]
    if len(annual) != expected:
        raise ValueError(f"Inventory contains {len(annual)} files; expected {expected}")

    seen = set()
    records = []
    missing = []
    for item in annual:
        key = (item["academic_year"], item["family"])
        if key in seen:
            raise ValueError(f"Duplicate inventory slot: {key}")
        seen.add(key)
        filename = item.get("local_filename")
        if not filename:
            missing.append({"academic_year": key[0], "family": key[1], "reason": "local_filename_missing"})
            continue
        path = input_dir / filename
        if not path.exists():
            missing.append({"academic_year": key[0], "family": key[1], "reason": "file_missing", "filename": filename})
            continue
        records.append({
            "academic_year": key[0],
            "family": key[1],
            "filename": filename,
            "sha256": sha256(path),
            "fingerprint": workbook_fingerprint(path),
        })

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
    for family in inventory["families"]:
        first = by_key[(inventory["window"]["first_academic_year"], family)]["fingerprint"]
        last = by_key[(inventory["window"]["last_academic_year"], family)]["fingerprint"]
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
