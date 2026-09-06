"""Extract registered Study B 2021 rows and evaluate four-year source coverage."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from pt_he_pipeline.study_b_2021_source import MEASURES, parse_comparative_section, programme_section

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data" / "curated" / "dges"
OUTPUT_DIR = ROOT / "results" / "study_b" / "2021_extension"
SOURCE_URL = "https://www.dges.gov.pt/guias/pdfs/statcol/2021/StatsCurso21.pdf"
PROGRAMMES = {
    "9081": ("Economia", "P24"),
    "9119": ("Engenharia Informática", "P43"),
    "9147": ("Gestão", "P55"),
    "9219": ("Psicologia", "P73"),
    "9500": ("Enfermagem", "P29"),
}
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


def _existing_source() -> pd.DataFrame:
    dtype = {"programme_code": str, "institution_code": str}
    frames = [pd.read_csv(SOURCE_DIR / name, dtype=dtype) for name in SOURCE_SHARDS]
    return pd.concat(frames, ignore_index=True)


def extract(text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for code, (name, page) in PROGRAMMES.items():
        section = programme_section(text, code=code, name=name)
        for row in parse_comparative_section(section, programme_code=code):
            if row.year != 2021:
                continue
            if row.prior_programme_code is not None and row.prior_programme_code != code:
                excluded.append(
                    {
                        "programme_code": code,
                        "institution_code": row.institution_code,
                        "institution_name": row.institution_name,
                        "prior_programme_code": row.prior_programme_code,
                        "reason": "different_programme_code_in_2020",
                    }
                )
                continue
            record: dict[str, object] = {
                "source_document_year": 2021,
                "source_url": SOURCE_URL,
                "source_pages": page,
                "source_section": f"{code} {name} [Licenciatura]",
                "source_type": "DGES StatsCurso comparative first-phase table",
                "provider_bytes_bundled": False,
                "year": 2021,
                "programme_code": code,
                "programme_name": name,
                "degree": "Licenciatura",
                "institution_code": row.institution_code,
                "institution_name": row.institution_name,
            }
            record.update({measure: value for measure, value in zip(MEASURES, row.values, strict=True)})
            records.append(record)
    return pd.DataFrame(records), pd.DataFrame(excluded)


def coverage(existing: pd.DataFrame, rows_2021: pd.DataFrame) -> pd.DataFrame:
    combined = pd.concat([existing, rows_2021], ignore_index=True)
    years = {2018, 2019, 2020, 2021}
    output: list[dict[str, object]] = []
    for code, (name, _) in PROGRAMMES.items():
        subset = combined.loc[combined["programme_code"] == code]
        counts = subset.groupby("institution_code")["year"].agg(lambda values: set(map(int, values)))
        stable = sorted(str(code_) for code_, observed in counts.items() if years.issubset(observed))
        output.append(
            {
                "programme_code": code,
                "programme_name": name,
                "stable_institutions_2018_2021": len(stable),
                "stable_institution_codes": "|".join(stable),
                "minimum_required": 6,
                "gate_passed": len(stable) >= 6,
            }
        )
    return pd.DataFrame(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path, help="pdftotext -layout output for StatsCurso21.pdf")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    text = args.text.read_text(encoding="utf-8", errors="replace")
    rows_2021, excluded = extract(text)
    gate = coverage(_existing_source(), rows_2021)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows_2021.to_csv(args.output_dir / "study_b_2021_candidate_source_rows.csv", index=False)
    excluded.to_csv(args.output_dir / "study_b_2021_code_transition_exclusions.csv", index=False)
    gate.to_csv(args.output_dir / "study_b_2018_2021_coverage_gate.csv", index=False)

    if rows_2021.empty:
        raise SystemExit("No eligible 2021 rows were extracted")
    if not bool(gate["gate_passed"].all()):
        failed = gate.loc[~gate["gate_passed"], ["programme_code", "stable_institutions_2018_2021"]]
        raise SystemExit(f"Four-year coverage gate failed:\n{failed.to_string(index=False)}")


if __name__ == "__main__":
    main()
