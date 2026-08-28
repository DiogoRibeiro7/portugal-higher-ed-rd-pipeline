"""Discover DGES annual-statistics documents for a range of years."""

from __future__ import annotations

import argparse
import json

from pt_he_pipeline.dges import discover_documents


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    args = parser.parse_args()
    if args.end < args.start:
        raise ValueError("--end must be greater than or equal to --start")

    results: dict[int, dict[str, str]] = {}
    for year in range(args.start, args.end + 1):
        try:
            results[year] = discover_documents(year)
        except Exception as exc:  # discovery report should preserve failed vintages
            results[year] = {"_error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
